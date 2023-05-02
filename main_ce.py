# Adapted from https://github.com/HobbitLong/SupContrast/blob/master/main_ce.py
# Removed syncBN related parts
# Changed val_loader num_workers form 8 to 2
# Removed tensorboard_logger parts for compatibility with Colab, instead added python lists to record accuracies and losses
# Added options for MINIST
# Added options for visualizing embeddings via t-SNE and PCA

from __future__ import print_function
import os
import sys
import argparse
import time
import math

import torch
import torch.backends.cudnn as cudnn
from torchvision import transforms, datasets
import torch.nn.functional as F

from util import AverageMeter
from util import adjust_learning_rate, warmup_learning_rate, accuracy
from util import set_optimizer, save_model
from resnet import SupCEResNet

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
    parser.add_argument('--epochs', type=int, default=500,
                        help='number of training epochs')

    # optimization
    parser.add_argument('--learning_rate', type=float, default=0.2,
                        help='learning rate')
    parser.add_argument('--lr_decay_epochs', type=str, default='350,400,450',
                        help='where to decay lr, can be a list')
    parser.add_argument('--lr_decay_rate', type=float, default=0.1,
                        help='decay rate for learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-4,
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
    parser.add_argument('--trial', type=str, default='0',
                        help='id for recording multiple runs')
    parser.add_argument('--visualize', action='store_false',
                        help='produce figures for the projections')

    opt = parser.parse_args()

    # set the path according to the environment
    opt.data_folder = './datasets/'
    opt.model_path = './save/SupCon/{}_models'.format(opt.dataset)
    opt.pic_path = './save/SupCon/{}_pic'.format(opt.dataset)

    iterations = opt.lr_decay_epochs.split(',')
    opt.lr_decay_epochs = list([])
    for it in iterations:
        opt.lr_decay_epochs.append(int(it))

    opt.model_name = 'SupCE_{}_{}_lr_{}_decay_{}_bsz_{}_trial_{}'.\
        format(opt.dataset, opt.model, opt.learning_rate, opt.weight_decay,
               opt.batch_size, opt.trial)

    if opt.cosine:
        opt.model_name = '{}_cosine'.format(opt.model_name)

    # warm-up for large-batch training,
    if opt.batch_size > 256:
        opt.warm = True
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

    opt.save_folder = os.path.join(opt.model_path, opt.model_name)
    if not os.path.isdir(opt.save_folder):
        os.makedirs(opt.save_folder)

    if opt.dataset == 'cifar10':
        opt.n_cls = 10
    elif opt.dataset == 'cifar100':
        opt.n_cls = 100
    elif opt.dataset == 'mnist':
        opt.n_cls = 10
    else:
        raise ValueError('dataset not supported: {}'.format(opt.dataset))
    return opt


def set_loader(opt):
    # construct data loader
    if opt.dataset == 'cifar10':
        mean = (0.4914, 0.4822, 0.4465)
        std = (0.2023, 0.1994, 0.2010)
    elif opt.dataset == 'cifar100':
        mean = (0.5071, 0.4867, 0.4408)
        std = (0.2675, 0.2565, 0.2761)
    elif opt.dataset == 'mnist':
        mean = (0.1307,)
        std = (0.3081,)
    else:
        raise ValueError('dataset not supported: {}'.format(opt.dataset))
    normalize = transforms.Normalize(mean=mean, std=std)

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(size=32, scale=(0.2, 1.)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        normalize,
    ])

    val_transform = transforms.Compose([
        transforms.ToTensor(),
        normalize,
    ])

    if opt.dataset == 'cifar10':
        train_dataset = datasets.CIFAR10(root=opt.data_folder,
                                         transform=train_transform,
                                         download=True)
        val_dataset = datasets.CIFAR10(root=opt.data_folder,
                                       train=False,
                                       transform=val_transform)
    elif opt.dataset == 'cifar100':
        train_dataset = datasets.CIFAR100(root=opt.data_folder,
                                          transform=train_transform,
                                          download=True)
        val_dataset = datasets.CIFAR100(root=opt.data_folder,
                                        train=False,
                                        transform=val_transform)
    elif opt.dataset == 'mnist':
        train_dataset = datasets.MNIST(root=opt.data_folder,
                                       transform=train_transform,
                                       download=True)
        val_dataset = datasets.MNIST(root=opt.data_folder,
                                     train=False,
                                     transform=val_transform)
    else:
        raise ValueError(opt.dataset)

    train_sampler = None
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=opt.batch_size, shuffle=(
            train_sampler is None),
        num_workers=opt.num_workers, pin_memory=True, sampler=train_sampler)
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=256, shuffle=False,
        num_workers=2, pin_memory=True)

    return train_loader, val_loader


def set_model(opt):
    model = SupCEResNet(name=opt.model, num_classes=opt.n_cls)
    criterion = torch.nn.CrossEntropyLoss()

    if torch.cuda.is_available():
        if torch.cuda.device_count() > 1:
            model = torch.nn.DataParallel(model)
        model = model.cuda()
        criterion = criterion.cuda()
        cudnn.benchmark = True

    return model, criterion


def train(train_loader, model, criterion, optimizer, epoch, opt):
    """one epoch training"""
    model.train()

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
        output = model(images)
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


def validate(val_loader, model, criterion, opt):
    """validation"""
    model.eval()

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
            output = model(images)
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
    model, criterion = set_model(opt)

    # build optimizer
    optimizer = set_optimizer(opt, model)

    # training routine
    avg_train_loss_history = []
    avg_train_acc_history = []
    avg_val_loss_history = []
    avg_val_acc_history = []
    for epoch in range(1, opt.epochs + 1):
        adjust_learning_rate(opt, optimizer, epoch)

        # train for one epoch
        time1 = time.time()
        loss, train_acc = train(train_loader, model,
                                criterion, optimizer, epoch, opt)
        time2 = time.time()
        print('epoch {}, total time {:.2f}'.format(epoch, time2 - time1))

        avg_train_loss_history.append(loss)
        avg_train_acc_history.append(train_acc)

        # evaluation
        loss, val_acc = validate(val_loader, model, criterion, opt)
        avg_val_acc_history.append(val_acc)
        avg_val_loss_history.append(loss)

        if val_acc > best_acc:
            best_acc = val_acc

        if epoch % opt.save_freq == 0:
            save_file = os.path.join(
                opt.save_folder, 'ckpt_epoch_{epoch}.pth'.format(epoch=epoch))
            save_model(model, optimizer, opt, epoch, save_file)

    # save the last model
    save_file = os.path.join(
        opt.save_folder, 'last.pth')
    save_model(model, optimizer, opt, opt.epochs, save_file)

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
