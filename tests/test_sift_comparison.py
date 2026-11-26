import unittest
import numpy as np
from ring_first_3d.sift_comparison.core import split_tracks, query_manifest, predict_queries, positive_similarity, transform_cameras, select_tuples

class ComparisonTests(unittest.TestCase):
    def test_split_is_disjoint_and_keeps_original_training(self):
        held=np.arange(31)%5==0
        s=split_tracks(held)
        self.assertEqual(s['train'],np.flatnonzero(~held).tolist())
        self.assertEqual(sorted(sum(s.values(),[])),list(range(31)))
        self.assertTrue(set(s['test']).isdisjoint(s['validation']))

    def test_query_never_fitted_and_missing_support_is_counted(self):
        xy=np.zeros((1,4,2)); manifest=query_manifest(xy,[0])
        calls=[]
        def triangle(poses,uv):
            calls.append(len(poses));return np.array([0.,0.,4.])
        def project(x,c,k):return np.zeros((len(x),2)),np.ones(len(x))
        c=np.repeat(np.eye(4)[None],4,0);c[:,0,3]=np.arange(4)
        out=predict_queries({'xy':xy,'category':np.array([1])},c,manifest,triangle,project,np.eye(3))
        self.assertEqual(calls,[3]*4)
        self.assertTrue(all(x['query'] not in x['support'] for x in out))
        c[0]=np.nan
        out=predict_queries({'xy':xy,'category':np.array([1])},c,manifest,triangle,project,np.eye(3))
        self.assertEqual(len(out),4)
        self.assertTrue(all(x['status']!='OK' for x in out))

    def test_positive_similarity_and_camera_transform(self):
        x=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,1],[2,1,3.]])
        r=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
        y=2*x@r.T+np.array([4,5,6])
        sim=positive_similarity(x,y)
        self.assertAlmostEqual(sim['scale'],2.)
        self.assertAlmostEqual(np.linalg.det(sim['rotation']),1.)
        c=np.repeat(np.eye(4)[None],2,0);c[1,:3,3]=[1,2,3]
        got=transform_cameras(c,sim)
        np.testing.assert_allclose(got[:,:3,3],2*c[:,:3,3]@r.T+[4,5,6],atol=1e-10)
        mirror=y.copy();mirror[:,0]*=-1
        self.assertGreater(np.linalg.det(positive_similarity(x,mirror)['rotation']),.999)

    def test_no_collinear_scale_alignment(self):
        x=np.repeat(np.arange(6)[:,None],3,axis=1)
        with self.assertRaises(ValueError):positive_similarity(x,x)

    def test_tuples_do_not_read_test_tracks(self):
        xy=np.zeros((20,5,2)); a=select_tuples(xy,list(range(16)))
        xy[16:]=np.nan
        self.assertEqual(a,select_tuples(xy,list(range(16))))
        self.assertEqual(len(a['tuples']),2)
        self.assertTrue(all(len(t['sources'])==3 and t['reference'] not in t['sources'] for t in a['tuples']))
