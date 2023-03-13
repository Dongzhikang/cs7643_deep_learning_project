Candidate Topics:

1. Xiaofei: 同学们，我初步想了一下做supervised contrastive learning. 主要就是重复这篇paper https://arxiv.org/abs/2004.11362. 我们可以另外测试一下其他的loss function。有点像这个人做的这样 https://towardsdatascience.com/contrasting-contrastive-loss-functions-3c13ca5f055e<br>
这个topic其实就跟这个课给的第一个idea相关了（Project 1: Learning from Unlabeled Data [Easy]，这个是做self-superivised contrastive learning, 我想做的这个是supervised）应该也是easy的. supervised contrastive learning这篇文章还是比较有名的，youtube上有很多解读的视频，比如这个(https://www.youtube.com/watch?v=MpdbFLXOOIw&t=639s)。说这么多就是觉得做这个topic应该不会有很大risk，并且可以学习contrastive learning.<br>
Project Summary: <br>
Contrastive learning aims to learn an embedding space in which raw input data are transformed such that similar samples become close together while dissimilar ones are far apart.  It has mainly been applied to self-supervised representation learning, leading to state of the art performances in transfer learning for some downstream computer vision tasks. In this project, we will explore contrastive learning in a supervised setting, allowing us to effectively leverage label information. <br>
Approach:<br>
Our main goal is to reproduce Khosla et al. 2020 [1], which invented a new loss termed SupCon that allows for multiple positives per anchor, thus adapting contrastive learning to the fully supervised setting. Their idea is to leverage class labels in the loss function, so that samples belonging to the same class (rather than augmented data of the anchor as in self-supervised contrastive learning) are considered similar and therefore are pulled together in the embedding space. Their learning framework consists of an encoder network followed by a projection network. Contrastive loss is applied using the output of the projection network, which is discarded after training, i.e., only using the representation after the encoder network for downstream tasks. <br>
In addition to reproduce the main supervised contrastive learning framework, in order to help us understand their (and other self-supervised contrastive learning frameworks’) design choices, we aim to do the following:<br>
1). Compare SupCon with pair loss (one positive or negative pair) [2], triplet loss (one positive sample + one negative sample per anchor) [3,4], N-pair loss (one positive sample + multiple negative samples per anchor) [5], and NT-Xent loss (one positive sample + multiple negative samples per anchor) [6].<br>
2). Examine the effect of normalization after the encoder network and the projection network (normalization is expected to improve downstream classification accuracy [4,7]).<br>
3). Examine the effect of data augmentation. Data augmentation via cropping, color distortion, Gaussian blurring, etc. is generally not applicable outside of computer vision. Since we are using class labels to define similarity here, can we skip data augmentation in the hope that this framework can be used outside computer vision?<br>
4). Examine the effect of projection layer (no projection vs linear projection vs simple MLP non-linear projection). Non-linear projection is expected to perform the best [6].<br>
Resources/Related Work:
[1] “Supervised Contrastive Learning”, Khosla et al., 2020.
[2] “Learning a Similarity Metric Discriminatively, with Application to Face Verification”, Chopra et al., 2020.
[3] “Distance Metric Learning for Large Margin Nearest Neighbor Classification”, Weinberger et al., 2009.
[4] “FaceNet: A Unified Embedding for Face Recognition and Clustering”, Schroff et al., 2015.
[5] “Improved Deep Metric Learning with Multi-class N-pair Loss Objective”, Sohn et al., 2016.
[6] “A Simple Framework for Contrastive Learning of Visual Representations”, Chen et al., 2020.
[7] “Understanding contrastive representation learning through alignment and uniformity on the hypersphere”, Wang et al., 2020.
Datasets:
CIFAR-100 https://www.cs.toronto.edu/~kriz/cifar.html

articles (including contrastive learning in general, contrastive losses, etc.)
https://ai.googleblog.com/2021/06/extending-contrastive-learning-to.html
https://wandb.ai/authors/scl/reports/Supervised-Contrastive-Larning--VmlldzoxMjA2MzQ
https://lilianweng.github.io/posts/2021-05-31-contrastive/
https://jamesmccaffrey.wordpress.com/?s=contrastive+learning
https://medium.com/@maksym.bekuzarov/losses-explained-contrastive-loss-f8f57fe32246
https://arxiv.org/abs/2010.05113 (a review paper on contrastive learning)
https://towardsdatascience.com/contrasting-contrastive-loss-functions-3c13ca5f055e
https://gowrishankar.info/blog/introduction-to-contrastive-loss-similarity-metric-as-an-objective-function/
https://gombru.github.io/2019/04/03/ranking_loss/

implementation
https://github.com/HobbitLong/SupContrast
https://www.kaggle.com/code/debarshichanda/pytorch-supervised-contrastive-learning

youtube
https://www.youtube.com/watch?v=MpdbFLXOOIw
https://www.youtube.com/watch?v=DQpcy4o2qFU
https://www.youtube.com/watch?v=o00oZmadBxA


2. Yunkai: 有一个想法 就是现在各种visualization method大部分看不到颜色 但是颜色不一定没有被用在feature recognition里面 所以可以讨论一下颜色对classification的影响 可以选几个比较出名的architecture然后把data都变成grayscale -> train models -> 然后用它去classify彩色的图片（或者反过来）然后hopefully可以在training data里面加几个颜色滤镜 最后提升识别的accuracy and robustness 这个好处是没有新的要学的知识 可能也不太需要太多调参 所有downside surprise比较小
