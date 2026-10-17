package OpenCV.Core is
   type Mat is tagged limited private;
   type Float32_Value is digits 6;
   function Convert (Source : Mat) return Mat;
end OpenCV.Core;
