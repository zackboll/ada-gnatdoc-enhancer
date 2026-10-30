with OpenCV.Core.Vectors;

--  One complete CV_8SC2 Mat element (2 bytes). Components 0 .. 1 are OpenCV
--  channel indices holding signed -128 .. 127 values; no semantic channel
--  meaning is assigned. OpenCV defines no named signed-8 Vec alias; the
--  unsigned Vec2b (uchar) alias is a different type.
package OpenCV.Core.Int8_Vec2 is new
  OpenCV.Core.Vectors (Element_Type => Int8_Value, Length => 2);
