with OpenCV.Core;
package OpenCV.Core.Sparse is
   type Sparse_Mat is limited private;
   function Convert (Source : OpenCV.Core.Mat) return Sparse_Mat;
end OpenCV.Core.Sparse;
