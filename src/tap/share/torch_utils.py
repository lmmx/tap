from torch.cuda import is_available as has_cuda

__all__ = ["device"]

device = "cuda:0" if has_cuda() else "cpu"
