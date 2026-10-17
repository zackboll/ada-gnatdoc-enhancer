with OpenCV.Core.Int16_Vec4;

--  Whole-row access to four-channel Int16 (CV_16SC4) two-dimensional Mats,
--  by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each element is one complete
--  OpenCV.Core.Int16_Vec4.Vector holding the four interleaved channel values
--  of one pixel. Row indices are zero-based. Every operation validates the
--  Mat's depth, channel count, dimension count, row index and row length and
--  raises OpenCV_Error on any mismatch.

package OpenCV.Core.Int16_Vec4_Row_Access is

   --  The values of one Mat row, one four-channel Vector per column. Array
   --  bounds are the caller's choice: only the length matters, and the first
   --  array element always corresponds to column 0. The zero-copy callbacks
   --  pass arrays whose bounds are 0 .. Image.Columns - 1.
   type Row_Array is array (Natural range <>) of Int16_Vec4.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0. Image is unchanged
   --  and Data owns its values.
   --  @param Image A two-dimensional Int16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one four-channel element per column.
   --  @exception OpenCV_Error Raised when Image is not an Int16 four-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional Int16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One four-channel element per column.
   --  @exception OpenCV_Error Raised when Image is not an Int16 four-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Invokes Process with a zero-copy view of one Int16 C4 Mat row. Data
   --  directly aliases native OpenCV storage for that logical row, with
   --  bounds 0 .. Image.Columns - 1; no pixel values are copied and only the
   --  active row elements are exposed. Data is valid only during Process and
   --  must not be retained.
   --  @param Image A two-dimensional Int16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Int16 four-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view. Writes
   --  through Data mutate the actual Mat storage immediately.
   --  @param Image A two-dimensional Int16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Int16 four-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));
end OpenCV.Core.Int16_Vec4_Row_Access;
