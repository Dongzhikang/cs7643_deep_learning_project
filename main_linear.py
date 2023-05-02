# Adapted from https://github.com/HobbitLong/SupContrast/blob/master/main_linear.py
# Removed syncBN related parts
# Added options for MNIST
# Added accuracy and loss curves
# Added options for visualizing embeddings via t-SNE and PCA


from __future__ import print_function

import sys
import argparse
import time
import math
import os

import torch
import torch.backends.cudnn as cudnn
import torch.nn.functional as F

from main_ce import set_loader
from util import AverageMeter
from util import adjust_learning_rate, warmup_learning_rate, accuracy
from util import set_optimizer
from resnet import SupConResNet, LinearClassifier


import matplotlib.pyplot as plt
from matplotlib import colormaps
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


def parse_option():
    parser = argparse.ArgumentParser('argument for training')

    parser.add_argument('--print_freq', type=int, default=10,
                        help='print frequency')
    parser.add_argument('--save_freq', type=int, default=50,
                        help='save frequency')
    parser.add_argument('--batch_size', type=int, default=256,
                        help='batch_size')
    parser.add_argument('--num_workers', type=int, default=16,
                        help='num of workers to use')
    parser.add_argument('--epochs', type=int, default=100,
                        help='number of training epochs')

    # optimization
    parser.add_argument('--learning_rate', type=float, default=0.1,
                        help='learning rate')
    parser.add_argument('--lr_decay_epochs', type=str, default='60,75,90',
                        help='where to decay lr, can be a list')
    parser.add_argument('--lr_decay_rate', type=float, default=0.2,
                        help='decay rate for learning rate')
    parser.add_argument('--weight_decay', type=float, default=0,
                        help='weight decay')
    parser.add_argument('--momentum', type=float, default=0.9,
                        help='momentum')

    # model dataset
    parser.add_argument('--model', type=str, default='resnet50')
    parser.add_argument('--dataset', type=str, default='cifar10',
                        choices=['cifar10', 'cifar100', 'mnist'], help='dataset')

    # other setting
    parser.add_argument('--cosine', action='store_true',
                        help='using cosine annealing')
    parser.add_argument('--warm', action='store_true',
                        help='warm-up for large batch training')

    parser.add_argument('--ckpt', type=str, default='',
                        help='path to pre-trained model')
    parser.add_argument('--visualize', action='store_false',
                        help='produce figures for the projections')

    opt = parser.parse_args()

    # set the path according to the environment
    opt.data_folder = './datasets/'
    opt.pic_path = './save/SupCon/{}_pic'.format(opt.dataset)

    iterations = opt.lr_decay_epochs.split(',')
    opt.lr_decay_epochs = list([])
    for it in iterations:
        opt.lr_decay_epochs.append(int(it))

    opt.model_name = '{}_{}_lr_{}_decay_{}_bsz_{}'.\
        format(opt.dataset, opt.model, opt.learning_rate, opt.weight_decay,
               opt.batch_size)

    if opt.cosine:
        opt.model_name = '{}_cosine'.format(opt.model_name)

    # warm-up for large-batch training,
    if opt.warm:
        opt.model_name = '{}_warm'.format(opt.model_name)
        opt.warmup_from = 0.01
        opt.warm_epochs = 10
        if opt.cosine:
            eta_min = opt.learning_rate * (opt.lr_decay_rate ** 3)
            opt.warmup_to = eta_min + (opt.learning_rate - eta_min) * (
                1 + math.cos(math.pi * opt.warm_epochs / opt.epochs)) / 2
        else:
            opt.warmup_to = opt.learning_rate

    opt.pic_folder = os.path.join(opt.pic_path, opt.model_name)
    if not os.path.isdir(opt.pic_folder):
        os.makedirs(opt.pic_folder)

    if opt.dataset == 'cifar10':
        opt.n_cls = 10
    elif opt.dataset == 'cifar100':
        opt.n_cls = 100
    elif opt.dataset == 'mnist':
        opt.n_cls = 10
    else:
        raise ValueError('dataset not supported: {}'.format(opt.dataset))

    return opt


def set_model(opt):
    model = SupConResNet(name=opt.model)
    criterion = torch.nn.CrossEntropyLoss()

    classifier = LinearClassifier(name=opt.model, num_classes=opt.n_cls)

    ckpt = torch.load(opt.ckpt, map_location='cpu')
    state_dict = ckpt['model']

    if torch.cuda.is_available():
        if torch.cuda.device_count() > 1:
            model.encoder = torch.nn.DataParallel(model.encoder)
        else:
            new_state_dict = {}
            for k, v in state_dict.items():
                k = k.replace("module.", "")
                new_state_dict[k] = v
            state_dict = new_state_dict
        model = model.cuda()
        classifier = classifier.cuda()
        criterion = criterion.cuda()
        cudnn.benchmark = True

        model.load_state_dict(state_dict)

    return model, classifier, criterion


def train(train_loader, model, classifier, criterion, optimizer, epoch, opt):
    """one epoch training"""
    model.eval()
    classifier.train()

    batch_time = AverageMeter()
    data_time = AverageMeter()
    losses = AverageMeter()
    top1 = AverageMeter()

    end = time.time()
    for idx, (images, labels) in enumerate(train_loader):
        data_time.update(time.time() - end)

        images = images.cuda(non_blocking=True)
        labels = labels.cuda(non_blocking=True)
        bsz = labels.shape[0]

        # warm-up learning rate
        warmup_learning_rate(opt, epoch, idx, len(train_loader), optimizer)

        # compute loss
        with torch.no_grad():
            features = model.encoder(images)
        output = classifier(features.detach())
        loss = criterion(output, labels)

        # update metric
        losses.update(loss.item(), bsz)
        acc1, acc5 = accuracy(output, labels, topk=(1, 5))
        top1.update(acc1[0], bsz)

        # SGD
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()

        # print info
        if (idx + 1) % opt.print_freq == 0:
            print('Train: [{0}][{1}/{2}]\t'
                  'BT {batch_time.val:.3f} ({batch_time.avg:.3f})\t'
                  'DT {data_time.val:.3f} ({data_time.avg:.3f})\t'
                  'loss {loss.val:.3f} ({loss.avg:.3f})\t'
                  'Acc@1 {top1.val:.3f} ({top1.avg:.3f})'.format(
                      epoch, idx + 1, len(train_loader), batch_time=batch_time,
                      data_time=data_time, loss=losses, top1=top1))
            sys.stdout.flush()

    return losses.avg, top1.avg


def validate(val_loader, model, classifier, criterion, opt):
    """validation"""
    model.eval()
    classifier.eval()

    batch_time = AverageMeter()
    losses = AverageMeter()
    top1 = AverageMeter()

    with torch.no_grad():
        end = time.time()
        for idx, (images, labels) in enumerate(val_loader):
            images = images.float().cuda()
            labels = labels.cuda()
            bsz = labels.shape[0]

            # forward
            output = classifier(model.encoder(images))
            loss = criterion(output, labels)

            # update metric
            losses.update(loss.item(), bsz)
            acc1, acc5 = accuracy(output, labels, topk=(1, 5))
            top1.update(acc1[0], bsz)

            # measure elapsed time
            batch_time.update(time.time() - end)
            end = time.time()

            if idx % opt.print_freq == 0:
                print('Test: [{0}/{1}]\t'
                      'Time {batch_time.val:.3f} ({batch_time.avg:.3f})\t'
                      'Loss {loss.val:.4f} ({loss.avg:.4f})\t'
                      'Acc@1 {top1.val:.3f} ({top1.avg:.3f})'.format(
                          idx, len(val_loader), batch_time=batch_time,
                          loss=losses, top1=top1))

    print(' * Acc@1 {top1.avg:.3f}'.format(top1=top1))
    return losses.avg, top1.avg


def main():
    best_acc = 0
    opt = parse_option()

    # build data loader
    train_loader, val_loader = set_loader(opt)

    # build model and criterion
    model, classifier, criterion = set_model(opt)

    # build optimizer
    optimizer = set_optimizer(opt, classifier)

    # training routine
    avg_train_loss_history = []
    avg_train_acc_history = []
    avg_val_loss_history = []
    avg_val_acc_history = []
    for epoch in range(1, opt.epochs + 1):
        adjust_learning_rate(opt, optimizer, epoch)

        # train for one epoch
        time1 = time.time()
        loss, acc = train(train_loader, model, classifier, criterion,
                          optimizer, epoch, opt)
        time2 = time.time()
        print('Train epoch {}, total time {:.2f}, accuracy:{:.2f}'.format(
            epoch, time2 - time1, acc))

        avg_train_loss_history.append(loss)
        avg_train_acc_history.append(acc)

        # eval for one epoch
        loss, val_acc = validate(val_loader, model, classifier, criterion, opt)
        avg_val_acc_history.append(val_acc)
        avg_val_loss_history.append(loss)
        if val_acc > best_acc:
            best_acc = val_acc

    print('best accuracy: {:.2f}'.format(best_acc))

    # save learning curves
    if torch.cuda.is_available():
        avg_train_acc_history = [x.cpu() for x in avg_train_acc_history]
        avg_val_acc_history = [x.cpu() for x in avg_val_acc_history]

    fig = plt.figure()
    plt.plot(np.arange(1, opt.epochs+1), avg_train_acc_history, label='train')
    plt.plot(np.arange(1, opt.epochs+1), avg_val_acc_history, label='val')
    plt.legend()
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.title("Accuracy curve")
    pic_file = os.path.join(opt.pic_folder, 'acc.png')
    plt.savefig(pic_file)

    fig = plt.figure()
    plt.plot(np.arange(1, opt.epochs+1), avg_train_loss_history, label='train')
    plt.plot(np.arange(1, opt.epochs+1), avg_val_loss_history, label='val')
    plt.legend()
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title("Loss curve")
    pic_file = os.path.join(opt.pic_folder, 'loss.png')
    plt.savefig(pic_file)

    # visualize the embedding
    if opt.visualize:
        # shape only works for resnet50 and resnet101!
        embeddings = np.zeros(shape=(0, 2048))
        labels = np.zeros(shape=(0))
        model.eval()
        with torch.no_grad():
            for image, label in iter(val_loader):
                image = image.float().cuda()
                emb = F.normalize(model.encoder(image), dim=1)
                labels = np.concatenate((labels, label.numpy().ravel()))
                embeddings = np.concatenate(
                    [embeddings, emb.detach().cpu().numpy()], axis=0)

        # create two dimensional t-SNE and PCA projections of the embeddings
        # adapted from https://towardsdatascience.com/visualizing-feature-vectors-embeddings-using-pca-and-t-sne-ef157cea3a42
        tsne = TSNE(2)
        tsne_proj = tsne.fit_transform(embeddings)
        cmap = colormaps['tab10']
        fig, ax = plt.subplots(figsize=(8, 8))
        for lab in range(opt.n_cls):
            indices = labels == lab
            ax.scatter(tsne_proj[indices, 0], tsne_proj[indices, 1], c=np.array(
                cmap(lab)).reshape(1, 4), label=lab, alpha=0.7)
        ax.legend()
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        plt.title("t-SNE projected embeddings")
        pic_file = os.path.join(opt.pic_folder, 'tsne.png')
        plt.savefig(pic_file)

        pca = PCA(n_components=2)
        pca_proj = pca.fit_transform(embeddings)
        fig, ax = plt.subplots(figsize=(8, 8))
        for lab in range(opt.n_cls):
            indices = labels == lab
            ax.scatter(pca_proj[indices, 0], pca_proj[indices, 1], c=np.array(
                cmap(lab)).reshape(1, 4), label=lab, alpha=0.7)
        ax.legend()
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        plt.title("PCA projected embeddings")
        pic_file = os.path.join(opt.pic_folder, 'pca.png')
        plt.savefig(pic_file)


if __name__ == '__main__':
    main()
