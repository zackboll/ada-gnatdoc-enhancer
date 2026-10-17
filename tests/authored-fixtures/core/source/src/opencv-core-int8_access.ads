--  Checked element access to single-channel Int8 (CV_8SC1) Mats. Each
--  element is one Int8_Value. Every operation validates the Mat's depth,
--  channel count, dimension count and indices before touching storage and
--  raises OpenCV_Error on any mismatch, so a wrong Mat type is never
--  reinterpreted. Indices are zero-based. Writes go to the Mat's actual
--  storage, so every shallow alias and the parent of a Region observe them.

package OpenCV.Core.Int8_Access is

   --  Reads the element at a zero-based row and column of a two-dimensional
   --  Mat.
   --  @param Image A two-dimensional Int8 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The stored element value.
   --  @exception OpenCV_Error Raised when Image is not an Int8 single-channel
   --  two-dimensional Mat, or Row or Column is outside the Mat.
   function Get (Image : Mat; Row, Column : Integer) return Int8_Value;

   --  Writes the element at a zero-based row and column of a two-dimensional
   --  Mat. The change is made in the Mat's actual storage and is visible
   --  through every header sharing it.
   --  @param Image A two-dimensional Int8 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is not an Int8 single-channel
   --  two-dimensional Mat, or Row or Column is outside the Mat.
   procedure Set
     (Image : in out Mat; Row, Column : Integer; Value : Int8_Value);

   --  Zero-based N-dimensional access. Indices'Length must equal
   --  Image.Dimension_Count. Iteration order maps to OpenCV dimensions
   --  regardless of the array's index bounds.
   --  @param Image An Int8 Mat with exactly one channel and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The stored element value.
   --  @exception OpenCV_Error Raised when Image is not an Int8 single-channel
   --  Mat, Indices does not have exactly one entry per dimension, or an
   --  index is out of range.
   function Get (Image : Mat; Indices : Index_Array) return Int8_Value;

   --  Zero-based N-dimensional write; the indexing rules of the matching Get
   --  apply. The change is made in the Mat's actual storage and is visible
   --  through every header sharing it.
   --  @param Image An Int8 Mat with exactly one channel and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is not an Int8 single-channel
   --  Mat, Indices does not have exactly one entry per dimension, or an
   --  index is out of range.
   procedure Set
     (Image : in out Mat; Indices : Index_Array; Value : Int8_Value);

end OpenCV.Core.Int8_Access;
