# cs7643_deep_learning_project
Final project for CS7643 Deep Learning

#### CE standard supervised learning
run `python main_ce.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon
pretraining: run `python main_supcon.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### NT-Xent
pretraining: run `python main_supcon.py --method SimCLR --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### N-pair
pretraining: run `python main_supcon.py --method SimCLR --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### Triplet
pretraining: run `python main_triplet_pair.py --method Triplet --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### Pair
pretraining: run `python main_triplet_pair.py --method Pair --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon with no projector
in resnet.py uncomment line 176 comment out line 178

pretraining: run `python main_supcon.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon with linear projector
change resnet.py line 158 `head='linear'`

pretraining: run `python main_supcon.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon with normalized encoder output and normalized projector output
in resnet.py uncomment line 176

pretraining: run `python main_supcon.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon with normalized encoder output and unnormalized projector output
in resnet.py uncomment line 176,177 comment out line 178

pretraining: run `python main_supcon.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon with unnormalized encoder output and unnormalized projector output
in resnet.py uncomment line 177 comment out line 178

pretraining: run `python main_supcon.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

#### SupCon without data augmentation
pretraining: run `python main_supcon_no_aug.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --temp 0.1 --model resnet50 --dataset cifar10`

linear evaluation: run `python main_linear.py --batch_size 256 --num_workers 2 --epochs 40 --learning_rate 0.05 --model resnet50 --dataset cifar10`

