package OpenCV.Geometry is
   type Point_2D is record X, Y : Long_Float; end record;
   function Transform (Value : Point_2D) return Point_2D;
   type Float32_Point_Array is array (Positive range <>) of Point_2D;
end OpenCV.Geometry;
