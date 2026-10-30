with OpenCV.Core.Int8_Vec3;

--  Typed access to three-channel signed 8-bit (CV_8SC3) Mats. One vector is
--  one complete 3-byte element; component 0 is channel 0. Every signed value
--  -128 .. 127 is preserved exactly. The Row/Column overloads require a 2-D
--  Mat. The Index_Array overloads require one zero-based index per Mat
--  dimension; iteration order maps to OpenCV dimension order regardless of
--  the array's bounds. Depth must be exactly Int8 and the channel count
--  exactly 3; violations raise OpenCV_Error.

package OpenCV.Core.Int8_Vec3_Access is

   --  Reads the complete element at a zero-based row and column of a
   --  two-dimensional Mat.
   --  @param Image A two-dimensional Int8 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The three channel values of the element.
   --  @exception OpenCV_Error Raised when Image is not an Int8 three-channel
   --  two-dimensional Mat, or Row or Column is outside the Mat.
   function Get (Image : Mat; Row, Column : Integer) return Int8_Vec3.Vector;

   --  Writes the complete element at a zero-based row and column of a
   --  two-dimensional Mat. All three channels are stored together, in the
   --  Mat's actual storage, and are visible through every header sharing it.
   --  @param Image A two-dimensional Int8 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The three channel values to store.
   --  @exception OpenCV_Error Raised when Image is not an Int8 three-channel
   --  two-dimensional Mat, or Row or Column is outside the Mat.
   procedure Set
     (Image : in out Mat; Row, Column : Integer; Value : Int8_Vec3.Vector);

   --  Reads the complete element at a zero-based N-dimensional index.
   --  Indices'Length must equal Image.Dimension_Count. One vector is one
   --  complete three-channel element.
   --  @param Image An Int8 Mat with exactly three channels and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The three channel values of the element.
   --  @exception OpenCV_Error Raised when Image is not an Int8 three-channel
   --  Mat, Indices does not have exactly one entry per dimension, or an
   --  index is out of range.
   function Get (Image : Mat; Indices : Index_Array) return Int8_Vec3.Vector;

   --  Zero-based N-dimensional write of one complete three-channel element;
   --  the indexing rules of the matching Get apply. All three channels are
   --  stored together, in the Mat's actual storage, and are visible through
   --  every header sharing it.
   --  @param Image An Int8 Mat with exactly three channels and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The three channel values to store.
   --  @exception OpenCV_Error Raised when Image is not an Int8 three-channel
   --  Mat, Indices does not have exactly one entry per dimension, or an
   --  index is out of range.
   procedure Set
     (Image : in out Mat; Indices : Index_Array; Value : Int8_Vec3.Vector);

end OpenCV.Core.Int8_Vec3_Access;
