with OpenCV.Core.Vectors;

--  One complete CV_8SC3 Mat element (3 bytes). Components 0 .. 2 are OpenCV
--  channel indices holding signed -128 .. 127 values; no semantic channel
--  meaning is assigned. OpenCV defines no named signed-8 Vec alias; the
--  unsigned Vec3b (uchar) alias is a different type.
package OpenCV.Core.Int8_Vec3 is new
  OpenCV.Core.Vectors (Element_Type => Int8_Value, Length => 3);
