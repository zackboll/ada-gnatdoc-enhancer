with OpenCV.Core.Float64_Vec3;

--  Whole-row access to three-channel Float64 (CV_64FC3) two-dimensional
--  Mats, by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each array element is one
--  complete three-channel pixel. Row indices are zero-based. Every operation
--  validates the Mat's depth, channel count, row index and row length and
--  raises OpenCV_Error on any mismatch.

package OpenCV.Core.Float64_Vec3_Row_Access is

   --  The values of one Mat row, one three-channel vector per column. Array
   --  bounds are the caller's choice: only the length matters, and the first
   --  array element always corresponds to column 0.
   type Row_Array is array (Natural range <>) of Float64_Vec3.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0. Image is
   --  unchanged and Data owns its values.
   --  @param Image A two-dimensional Float64 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one three-channel vector per column.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  three-channel Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional Float64 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One three-channel vector per column.
   --  @exception OpenCV_Error Raised when Image is not a Float64
   --  three-channel Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Callback-scoped zero-copy row, including non-contiguous Regions.
   --  A shallow Mat lease protects storage. Do not retain Data afterward.
   --  Data is indexed from 0 with Data'Length = Image.Columns.
   --  @param Image A two-dimensional Float64 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float64 three-channel Mat or Row is outside
   --  the Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view. Writes
   --  through Data mutate the actual Mat storage immediately.
   --  @param Image A two-dimensional Float64 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float64 three-channel Mat or Row is outside
   --  the Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));
end OpenCV.Core.Float64_Vec3_Row_Access;
