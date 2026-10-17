with OpenCV.Core.Vectors;

--  One complete CV_16FC3 Mat element. Components 0 .. 2 are OpenCV channel
--  indices holding exact IEEE-754 binary16 encodings (Float16_Value); no
--  semantic channel meaning is assigned.
package OpenCV.Core.Float16_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => Float16_Value, Length => 3);
