with OpenCV.Core.Float16_Vec3;

--  Checked element access to three-channel Float16 (CV_16FC3) Mats. Each
--  element is one OpenCV.Core.Float16_Vec3.Vector holding the three
--  interleaved channel values of one complete pixel in native channel order.
--  Each component is the exact stored IEEE-754 binary16 encoding: signed
--  zeros, subnormals, infinities and NaN payloads are preserved and never
--  converted. Every operation validates the Mat's depth, channel count,
--  dimension count and indices before touching storage and raises
--  OpenCV_Error on any mismatch. Indices are zero-based. Writes go to the
--  Mat's actual storage, so every shallow alias and the parent of a Region
--  observe them.

package OpenCV.Core.Float16_Vec3_Access is

   --  Reads the complete element at a zero-based row and column of a
   --  two-dimensional Mat.
   --  @param Image A two-dimensional Float16 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The three channel values of the element, with exact bits.
   --  @exception OpenCV_Error Raised when Image is not a Float16
   --  three-channel two-dimensional Mat, or Row or Column is outside the Mat.
   function Get
     (Image : Mat; Row, Column : Integer)
      return OpenCV.Core.Float16_Vec3.Vector;

   --  Writes the complete element at a zero-based row and column of a
   --  two-dimensional Mat. All three channels are stored together, in
   --  the Mat's actual storage, and are visible through every header sharing
   --  it.
   --  @param Image A two-dimensional Float16 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The three channel values to store.
   --  @exception OpenCV_Error Raised when Image is not a Float16
   --  three-channel two-dimensional Mat, or Row or Column is outside the Mat.
   procedure Set
     (Image  : in out Mat;
      Row    : Integer;
      Column : Integer;
      Value  : OpenCV.Core.Float16_Vec3.Vector);

   --  Zero-based N-dimensional access. Indices'Length must equal
   --  Image.Dimension_Count. Iteration order maps to OpenCV dimensions
   --  regardless of the array's index bounds. One vector is one complete
   --  three-channel element. Component encodings stay exact binary16 bits.
   --  @param Image A Float16 Mat with exactly three channels and at least
   --  one dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The three channel values of the element, with exact bits.
   --  @exception OpenCV_Error Raised when Image is not a Float16
   --  three-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   function Get
     (Image : Mat; Indices : Index_Array)
      return OpenCV.Core.Float16_Vec3.Vector;

   --  Zero-based N-dimensional write of one complete three-channel element;
   --  the indexing rules of the matching Get apply. All three channels are
   --  stored together, in the Mat's actual storage, and are visible through
   --  every header sharing it.
   --  @param Image A Float16 Mat with exactly three channels and at least
   --  one dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The three channel values to store.
   --  @exception OpenCV_Error Raised when Image is not a Float16
   --  three-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   procedure Set
     (Image   : in out Mat;
      Indices : Index_Array;
      Value   : OpenCV.Core.Float16_Vec3.Vector);

end OpenCV.Core.Float16_Vec3_Access;
