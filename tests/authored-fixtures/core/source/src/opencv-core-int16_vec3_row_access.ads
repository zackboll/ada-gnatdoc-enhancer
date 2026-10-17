with OpenCV.Core.Int16_Vec3;

--  Whole-row access to three-channel Int16 (CV_16SC3) two-dimensional Mats,
--  by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each element is one complete
--  OpenCV.Core.Int16_Vec3.Vector holding the three interleaved channel
--  values of one pixel. Row indices are zero-based. Every operation
--  validates the Mat's depth, channel count, dimension count, row index and
--  row length and raises OpenCV_Error on any mismatch.

package OpenCV.Core.Int16_Vec3_Row_Access is

   --  The values of one Mat row, one three-channel Vector per column. Array
   --  bounds are the caller's choice: only the length matters, and the first
   --  array element always corresponds to column 0. The zero-copy callbacks
   --  pass arrays whose bounds are 0 .. Image.Columns - 1.
   type Row_Array is array (Natural range <>) of Int16_Vec3.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0. Image is unchanged
   --  and Data owns its values.
   --  @param Image A two-dimensional Int16 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one three-channel element per column.
   --  @exception OpenCV_Error Raised when Image is not an Int16 three-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional Int16 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One three-channel element per column.
   --  @exception OpenCV_Error Raised when Image is not an Int16 three-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Invokes Process with a zero-copy view of one Int16 C3 Mat row. Data
   --  directly aliases native OpenCV storage for that logical row, with
   --  bounds 0 .. Image.Columns - 1; no pixel values are copied and only the
   --  active row elements are exposed. Data is valid only during Process and
   --  must not be retained.
   --  @param Image A two-dimensional Int16 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Int16 three-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view. Writes
   --  through Data mutate the actual Mat storage immediately.
   --  @param Image A two-dimensional Int16 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Int16 three-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));
end OpenCV.Core.Int16_Vec3_Row_Access;
