with OpenCV.Core.Float32_Vec2;

--  Whole-row access to two-channel Float32 (CV_32FC2) two-dimensional Mats,
--  by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each row element is one complete
--  Float32_Vec2.Vector holding the two interleaved channel values of one
--  pixel. Row and column indices are zero-based. Every operation validates
--  the Mat's depth, channel count, row index and row length and raises
--  OpenCV_Error on any mismatch.

package OpenCV.Core.Float32_Vec2_Row_Access is
   --  Zero-based column position within a row.
   subtype Column_Index is Natural;

   --  The pixels of one Mat row, one Float32_Vec2.Vector per column. Array
   --  bounds are the caller's choice: only the length matters, and the first
   --  array element always corresponds to column 0.
   type Row_Array is array (Natural range <>) of Float32_Vec2.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0. Image is
   --  unchanged and Data owns its values.
   --  @param Image A two-dimensional Float32 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one two-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a Float32 two-channel
   --  Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional Float32 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One two-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a Float32 two-channel
   --  Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Borrowed storage is valid only during Process; no references may escape.
   --  Invokes Process with a zero-copy view of one Float32 C2 Mat row. Data
   --  aliases native storage for that row, one complete pixel per element, and
   --  is indexed with zero-based columns (Data'Length = Image.Columns).
   --  @param Image A two-dimensional Float32 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float32 two-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view; writes
   --  through Data mutate the actual Mat storage immediately.
   --  @param Image A two-dimensional Float32 Mat with exactly two channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float32 two-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));
end OpenCV.Core.Float32_Vec2_Row_Access;
