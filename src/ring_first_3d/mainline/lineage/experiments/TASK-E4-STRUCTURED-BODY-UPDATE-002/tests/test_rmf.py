import unittest,torch
from rmf import double_reflection
class RMFTests(unittest.TestCase):
 def curve(self):
  s=torch.linspace(-1,1,16,dtype=torch.float64);return torch.stack([s,.2*s**3,.1*s*s],1)
 def test_orthogonality_and_inflection_continuity(self):
  r,s,t=double_reflection(self.curve());F=torch.stack([r,s,t],-1);torch.testing.assert_close(F.transpose(1,2)@F,torch.eye(3,dtype=F.dtype).expand(16,3,3),atol=1e-12,rtol=0);self.assertGreater(float((r[1:]*r[:-1]).sum(1).min()),.9)
 def test_degenerate_rejected(self):
  with self.assertRaisesRegex(ValueError,'DEGENERATE'):double_reflection(torch.zeros((16,3),dtype=torch.float64))
 def test_gradient(self):
  C=self.curve();a=torch.tensor(.2,dtype=torch.float64,requires_grad=True)
  self.assertTrue(torch.autograd.gradcheck(lambda x:sum((z*torch.arange(48,dtype=z.dtype).reshape(16,3)).sum()for z in double_reflection(C+torch.sin(C)*x)),(a,),eps=1e-6,atol=1e-5))
