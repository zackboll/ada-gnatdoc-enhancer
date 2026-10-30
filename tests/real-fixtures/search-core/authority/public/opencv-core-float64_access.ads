--  Checked element access to single-channel Float64 (CV_64FC1) Mats. Each
--  element is one Float64_Value. Every operation validates the Mat's depth,
--  channel count, dimension count and indices before touching storage and
--  raises OpenCV_Error on any mismatch, so a wrong Mat type is never
--  reinterpreted. Indices are zero-based. Writes go to the Mat's actual
--  storage, so every shallow alias and the parent of a Region observe them.

package OpenCV.Core.Float64_Access is

   --  Result of Classify: the IEEE binary64 class of one stored element.
   --  @enum Finite The value is neither an infinity nor a NaN; zeros and
   --  subnormals are finite.
   --  @enum Positive_Infinity The value is positive infinity.
   --  @enum Negative_Infinity The value is negative infinity.
   --  @enum Not_A_Number The value is a NaN of any sign or payload.
   type Float64_Classification is
     (Finite, Positive_Infinity, Negative_Infinity, Not_A_Number);

   --  Reads the element at a zero-based row and column of a two-dimensional
   --  Mat.
   --  @param Image A two-dimensional Float64 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The stored element value.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  single-channel two-dimensional Mat, or Row or Column is outside the
   --  Mat.
   function Get (Image : Mat; Row, Column : Integer) return Float64_Value;

   --  Classifies the stored Float64 value without converting non-finite IEEE
   --  values into the public Float64_Value subtype.
   --  @param Image A two-dimensional Float64 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return Finite, Positive_Infinity, Negative_Infinity or Not_A_Number
   --  according to the stored element.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  single-channel two-dimensional Mat, Row or Column is outside the Mat,
   --  or the native classification fails.
   function Classify
     (Image : Mat; Row, Column : Integer) return Float64_Classification;

   --  Writes the element at a zero-based row and column of a two-dimensional
   --  Mat. The change is made in the Mat's actual storage and is visible
   --  through every header sharing it.
   --  @param Image A two-dimensional Float64 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  single-channel two-dimensional Mat, or Row or Column is outside the
   --  Mat.
   procedure Set
     (Image : in out Mat; Row, Column : Integer; Value : Float64_Value);

   --  Zero-based N-dimensional access. Indices'Length must equal
   --  Image.Dimension_Count. Iteration order maps to OpenCV dimensions
   --  regardless of the array's index bounds.
   --  @param Image A Float64 Mat with exactly one channel and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The stored element value.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  single-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   function Get (Image : Mat; Indices : Index_Array) return Float64_Value;

   --  Zero-based N-dimensional write; the indexing rules of the matching Get
   --  apply. The change is made in the Mat's actual storage and is visible
   --  through every header sharing it.
   --  @param Image A Float64 Mat with exactly one channel and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  single-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   procedure Set
     (Image : in out Mat; Indices : Index_Array; Value : Float64_Value);

end OpenCV.Core.Float64_Access;
