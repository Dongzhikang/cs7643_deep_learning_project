# cs7643_deep_learning_project
Final project for CS7643 Deep Learning

Run main_npair.py: main_npair.py --batch_size 128 --num_workers 2 --epochs 20 --learning_rate 0.05 --model 'resnet50' --dataset 'cifar10' --temp 0.1 --method NPair

Run main_triplet: main_triplet.py --batch_size 128 --num_workers 2 --epochs 20 --learning_rate 0.05 --model 'resnet50' --dataset 'cifar10' --temp 0.1 --method Triplet

Run main_ntxent: main_ntxent.py --batch_size 128 --num_workers 2 --epochs 20 --learning_rate 0.05 --model 'resnet50' --dataset 'cifar10' --temp 0.1 --method NTXent