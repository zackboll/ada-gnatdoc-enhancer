with OpenCV.Core.Vectors;

--  One complete CV_16FC4 Mat element. Components 0 .. 3 are OpenCV channel
--  indices holding exact IEEE-754 binary16 encodings (Float16_Value); no
--  semantic channel meaning is assigned.
package OpenCV.Core.Float16_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => Float16_Value, Length => 4);
