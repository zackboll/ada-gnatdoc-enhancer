with OpenCV.Core.Vectors;

--  One complete CV_8SC4 Mat element (4 bytes). Components 0 .. 3 are OpenCV
--  channel indices holding signed -128 .. 127 values; no semantic channel
--  meaning is assigned. OpenCV defines no named signed-8 Vec alias; the
--  unsigned Vec4b (uchar) alias is a different type.
package OpenCV.Core.Int8_Vec4 is new
  OpenCV.Core.Vectors (Element_Type => Int8_Value, Length => 4);
