with OpenCV.Core.Float16_Vec4;

--  Exact-bit typed access to four-channel Float16 (CV_16FC4) Mats. One vector
--  is one complete 8-byte element; components 0 .. 3 are channels 0 .. 3.
--  Each component is the stored IEEE-754 binary16 encoding: signed zeros,
--  subnormals, infinities and NaN payloads (including signaling NaNs) are
--  never converted or canonicalized. The Row/Column overloads require a 2-D
--  Mat. The Index_Array overloads require one zero-based index per Mat
--  dimension; iteration order maps to OpenCV dimension order regardless of
--  the array's bounds. Depth must be exactly Float16 and the channel count
--  exactly 4; violations raise OpenCV_Error.

package OpenCV.Core.Float16_Vec4_Access is

   --  Reads the complete element at a zero-based row and column of a
   --  two-dimensional Mat.
   --  @param Image A two-dimensional Float16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The four channel values of the element, with exact bits.
   --  @exception OpenCV_Error Raised when Image is not a Float16 four-channel
   --  two-dimensional Mat, or Row or Column is outside the Mat.
   function Get
     (Image : Mat; Row, Column : Integer) return Float16_Vec4.Vector;

   --  Writes the complete element at a zero-based row and column of a
   --  two-dimensional Mat. All four channels are stored together, with their
   --  exact bits, in the Mat's actual storage and are visible through every
   --  header sharing it.
   --  @param Image A two-dimensional Float16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The four channel values to store.
   --  @exception OpenCV_Error Raised when Image is not a Float16 four-channel
   --  two-dimensional Mat, or Row or Column is outside the Mat.
   procedure Set
     (Image : in out Mat; Row, Column : Integer; Value : Float16_Vec4.Vector);

   --  Reads the complete element at a zero-based N-dimensional position.
   --  Indices'Length must equal Image.Dimension_Count.
   --  @param Image A Float16 Mat with exactly four channels and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The four channel values of the element, with exact bits.
   --  @exception OpenCV_Error Raised when Image is not a Float16 four-channel
   --  Mat, Indices does not have exactly one entry per dimension, or an
   --  index is out of range.
   function Get
     (Image : Mat; Indices : Index_Array) return Float16_Vec4.Vector;

   --  Zero-based N-dimensional write of one complete four-channel element;
   --  the indexing rules of the matching Get apply. All four channels are
   --  stored together, in the Mat's actual storage, and are visible through
   --  every header sharing it.
   --  @param Image A Float16 Mat with exactly four channels and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The four channel values to store.
   --  @exception OpenCV_Error Raised when Image is not a Float16 four-channel
   --  Mat, Indices does not have exactly one entry per dimension, or an
   --  index is out of range.
   procedure Set
     (Image : in out Mat; Indices : Index_Array; Value : Float16_Vec4.Vector);
end OpenCV.Core.Float16_Vec4_Access;
