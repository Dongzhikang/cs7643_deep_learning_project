Candidate Topics:

1. Xiaofei: 同学们，我初步想了一下做supervised contrastive learning. 主要就是重复这篇paper https://arxiv.org/abs/2004.11362. 我们可以另外测试一下其他的loss function。有点像这个人做的这样 https://towardsdatascience.com/contrasting-contrastive-loss-functions-3c13ca5f055e
2. Yunkai: 有一个想法 就是现在各种visualization method大部分看不到颜色 但是颜色不一定没有被用在feature recognition里面 所以可以讨论一下颜色对classification的影响 可以选几个比较出名的architecture然后把data都变成grayscale -> train models -> 然后用它去classify彩色的图片（或者反过来）然后hopefully可以在training data里面加几个颜色滤镜 最后提升识别的accuracy and robustness 这个好处是没有新的要学的知识 可能也不太需要太多调参 所有downside surprise比较小
