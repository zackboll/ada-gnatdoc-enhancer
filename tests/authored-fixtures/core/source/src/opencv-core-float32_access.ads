--  Checked element access to single-channel Float32 (CV_32FC1) Mats. Each
--  element is one Float32_Value. Every operation validates the Mat's depth,
--  channel count, dimension count and indices before touching storage and
--  raises OpenCV_Error on any mismatch, so a wrong Mat type is never
--  reinterpreted. Indices are zero-based. Writes go to the Mat's actual
--  storage, so every shallow alias and the parent of a Region observe them.
--  Classify reports whether a stored element is finite, an infinity or NaN.

package OpenCV.Core.Float32_Access is

   --  Result of classifying one stored Float32 element.
   --  @enum Finite The value is neither an infinity nor a NaN; zeros and
   --  subnormals are finite.
   --  @enum Positive_Infinity The value is positive infinity.
   --  @enum Negative_Infinity The value is negative infinity.
   --  @enum Not_A_Number The value is a NaN of any sign or payload.
   type Float32_Classification is
     (Finite, Positive_Infinity, Negative_Infinity, Not_A_Number);

   --  Reads the element at a zero-based row and column of a two-dimensional
   --  Mat.
   --  @param Image A two-dimensional Float32 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return The stored element value.
   --  @exception OpenCV_Error Raised when Image is not a Float32
   --  single-channel Mat, or Row or Column is outside the Mat.
   function Get (Image : Mat; Row, Column : Integer) return Float32_Value;

   --  Classifies the stored Float32 value without converting non-finite IEEE
   --  values into the public Float32_Value subtype.
   --  @param Image A two-dimensional Float32 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @return Finite, Positive_Infinity, Negative_Infinity or Not_A_Number
   --  for the stored element.
   --  @exception OpenCV_Error Raised when Image is not a Float32
   --  single-channel Mat, Row or Column is outside the Mat, or the native
   --  classification fails.
   function Classify
     (Image : Mat; Row, Column : Integer) return Float32_Classification;

   --  Writes the element at a zero-based row and column of a two-dimensional
   --  Mat. The change is made in the Mat's actual storage and is visible
   --  through every header sharing it.
   --  @param Image A two-dimensional Float32 Mat with exactly one channel.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Column Zero-based column, in 0 .. Image.Columns - 1.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is not a Float32
   --  single-channel Mat, or Row or Column is outside the Mat.
   procedure Set
     (Image : in out Mat; Row, Column : Integer; Value : Float32_Value);

   --  Zero-based N-dimensional access. Indices'Length must equal
   --  Image.Dimension_Count. Iteration order maps to OpenCV dimensions
   --  regardless of the array's index bounds.
   --  @param Image A Float32 Mat with exactly one channel and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The stored element value.
   --  @exception OpenCV_Error Raised when Image is not a Float32
   --  single-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   function Get (Image : Mat; Indices : Index_Array) return Float32_Value;

   --  Zero-based N-dimensional write; the indexing rules of the matching Get
   --  apply. The change is made in the Mat's actual storage and is visible
   --  through every header sharing it.
   --  @param Image A Float32 Mat with exactly one channel and at least one
   --  dimension.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The element value to store.
   --  @exception OpenCV_Error Raised when Image is not a Float32
   --  single-channel Mat, Indices does not have exactly one entry per
   --  dimension, or an index is out of range.
   procedure Set
     (Image : in out Mat; Indices : Index_Array; Value : Float32_Value);

end OpenCV.Core.Float32_Access;
