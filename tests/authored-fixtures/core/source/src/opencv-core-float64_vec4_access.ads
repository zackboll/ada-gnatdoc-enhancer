with OpenCV.Core.Float64_Vec4;

--  Checked element access to four-channel Float64 (CV_64FC4) Mats. Each
--  element is one OpenCV.Core.Float64_Vec4.Vector holding the four
--  interleaved channel values of one complete pixel in native channel order.
--  Every operation validates the Mat's depth, channel count, dimension count
--  and indices before touching storage and raises OpenCV_Error on any
--  mismatch. Indices are zero-based. Writes go to the Mat's actual storage,
--  so every shallow alias and the parent of a Region observe them.

package OpenCV.Core.Float64_Vec4_Access is

   --  Reads the complete element at a zero-based row and column of a
   --  two-dimensional Mat.
   --  @param Image A two-dimensional Float64 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The four channel values of the element.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  four-channel two-dimensional Mat, or Row or Column is outside the
   --  Mat.
   function Get
     (Image : Mat; Row, Column : Integer) return Float64_Vec4.Vector;

   --  Writes the complete element at a zero-based row and column of a
   --  two-dimensional Mat. All four channels are stored together, in the
   --  Mat's actual storage, and are visible through every header sharing it.
   --  @param Image A two-dimensional Float64 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The four channel values to store.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  four-channel two-dimensional Mat, or Row or Column is outside the
   --  Mat.
   procedure Set
     (Image : in out Mat; Row, Column : Integer; Value : Float64_Vec4.Vector);

   --  Zero-based N-dimensional access. Indices'Length must equal
   --  Image.Dimension_Count. One vector is one complete four-channel
   --  element.
   --  @param Image A Float64 Mat with exactly four channels and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The four channel values of the element.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  four-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   function Get
     (Image : Mat; Indices : Index_Array) return Float64_Vec4.Vector;

   --  Zero-based N-dimensional write of one complete four-channel element;
   --  the indexing rules of the matching Get apply. All four channels are
   --  stored together, in the Mat's actual storage, and are visible through
   --  every header sharing it.
   --  @param Image A Float64 Mat with exactly four channels and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The four channel values to store.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  four-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   procedure Set
     (Image : in out Mat; Indices : Index_Array; Value : Float64_Vec4.Vector);
end OpenCV.Core.Float64_Vec4_Access;
