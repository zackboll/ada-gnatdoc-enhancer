with OpenCV.Core.Vectors;

--  One complete CV_16FC2 Mat element. Components 0 .. 1 are OpenCV channel
--  indices holding exact IEEE-754 binary16 encodings (Float16_Value); no
--  semantic channel meaning is assigned.
package OpenCV.Core.Float16_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => Float16_Value, Length => 2);
