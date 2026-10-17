with Ada.Finalization;
private with OpenCV.Internal.C_API;

--  OpenCV XML/YAML/JSON persistence for named values and nested
--  mappings and sequences.
--
--  File_Storage reads or writes named Mat, Integer, Long_Float, and
--  String values, plus nested mappings and sequences of those values.
--  Disk Open selects the format from the filename extension: .xml,
--  .yml, .yaml, or .json. Create_Memory writes to an in-memory buffer
--  in an explicit XML, YAML, or JSON format. Open_Memory reads a
--  previously serialized document and lets OpenCV auto-detect the
--  format from the text. Gzip, append, explicit disk format flags,
--  comments, FLOW formatting, custom type names,
--  and a public FileNode API are not part of this slice.
--
--  File_Storage is limited and not copyable. Exactly one Ada object
--  owns the underlying OpenCV FileStorage, which is released when the
--  Ada object is finalized. Hierarchy is navigated through
--  File_Storage itself; FileNode never appears in the public API.
--
--  The FileStorage root is an implicit mapping. Named Write,
--  Begin_Map, Begin_Sequence, Read_*, Enter_Map, and Enter_Sequence
--  are valid at root or inside a mapping. Unnamed Begin_Map /
--  Begin_Sequence, Append, indexed Read_*, indexed Enter_*, and
--  Sequence_Length are valid only inside a sequence. End_Structure
--  and Leave_Structure cannot close or leave the implicit root.
--
--  Write borrows the source value for the duration of the call and does
--  not modify it. Read operations return independently owned Ada values
--  that remain valid after the storage is finalized. A missing name
--  raises OpenCV_Error. Stored 0, 0.0, empty String, empty Mat, and
--  empty sequence values remain distinguishable from absence. Empty
--  mapping preservation depends on OpenCV and the persistence format;
--  a node parsed as a mapping with no entries has Map_Length zero.
--
--  Integer persistence uses OpenCV's signed 32-bit integer file node.
--  Write rejects an Ada Integer outside that domain with OpenCV_Error
--  rather than leaking Constraint_Error from a narrowing conversion.
--  With OpenCV 4.10, Write cannot persist -2_147_483_648 because
--  OpenCV's integer formatter uses abs(int); the supported write range
--  is -2_147_483_647 .. 2_147_483_647. This is an OpenCV 4.10 writer
--  limitation, not an Ada or file-format limitation.
--  Read_Integer requires an actual integer node and does not round a
--  real node.
--
--  Long_Float is persisted through OpenCV double. Read_Real accepts a
--  real node or safely widens an integer node to Long_Float. Other
--  node types are rejected.
--
--  Read_String requires an actual string node and does not stringify
--  numeric values. OpenCV 4.10 persistence emitters measure string
--  values with strlen, so Write rejects an embedded NUL in a String
--  value. Node names, filenames, and memory-read text also reject
--  embedded NUL because they cross a NUL-terminated ABI. OpenCV 4.10
--  memory-read measures the document with strlen.
--
--  Sequence indices are zero-based and match OpenCV FileNode
--  indexing. An out-of-range index raises OpenCV_Error.
--
--  Close_And_Get_Text finalizes a memory Write_Only storage and
--  returns the complete serialized document as an independently owned
--  Ada String. The storage is then closed. Disk storage, memory
--  readers, and writers with unclosed structures reject
--  Close_And_Get_Text without closing the storage.
--
--  Non-contiguous Mats are supported.

package OpenCV.Core.Persistence is

   --  Structural OpenCV FileNode category, not a high-level object type.
   --  A persisted Mat is a mapping (Mapping_Node); Read_Mat performs the
   --  explicit Mat conversion. No FileNode object or iterator is exposed.
   --  @enum Integer_Node A signed 32-bit integer node, read by Read_Integer.
   --  @enum Real_Node A floating-point node, read by Read_Real.
   --  @enum String_Node A string node, read by Read_String.
   --  @enum Sequence_Node An ordered sequence, entered by Enter_Sequence.
   --  @enum Mapping_Node A mapping of names to nodes, entered by Enter_Map.
   --  A serialized Mat is also reported as Mapping_Node.
   type Node_Kind is
     (Integer_Node, Real_Node, String_Node, Sequence_Node, Mapping_Node);

   --  Direction in which a File_Storage was opened. It is fixed for the
   --  life of the storage.
   --  @enum Read_Only The storage is parsed from a file or text and supports
   --  the Read, Enter, Kind and length operations.
   --  @enum Write_Only The storage is written and supports the Write,
   --  Begin, Append and End operations.
   type Storage_Mode is (Read_Only, Write_Only);

   --  Serialization format of a memory-backed writer created by
   --  Create_Memory.
   --  @enum XML The document is serialized as XML.
   --  @enum YAML The document is serialized as YAML.
   --  @enum JSON The document is serialized as JSON.
   type Storage_Format is (XML, YAML, JSON);

   --  Handle to an OpenCV FileStorage opened for reading or writing, from a
   --  disk file or an in-memory buffer. File_Storage is limited, so it cannot
   --  be copied or assigned: exactly one Ada object owns the native storage,
   --  and finalization of that object closes it. The object keeps a current
   --  read or write context (the implicit root, a mapping, or a sequence)
   --  that the Enter, Begin, Leave and End operations move. Operations
   --  that do not suit the opened Storage_Mode or the current context raise
   --  OpenCV_Error.
   type File_Storage is new Ada.Finalization.Limited_Controlled with private;

   --  Opens Filename for reading or writing. Format is selected from
   --  the filename extension. Raises OpenCV_Error if Filename is empty,
   --  contains an embedded NUL, or cannot be opened. Write_Only follows
   --  cv::FileStorage WRITE mode, which creates the file or replaces an
   --  existing one; the document is completed when the storage is finalized.
   --  @param Filename Path whose extension (.xml, .yml, .yaml or .json)
   --  selects the format.
   --  @param Mode Whether the file is read or written.
   --  @return An open File_Storage positioned at the implicit root.
   --  @exception OpenCV_Error Raised when Filename is empty, contains an
   --  embedded NUL, or cannot be opened.
   function Open (Filename : String; Mode : Storage_Mode) return File_Storage;

   --  Creates an open Write_Only memory-backed File_Storage that
   --  serializes to Format. No file is created. Existing Write
   --  operations work unchanged. Close_And_Get_Text returns the
   --  serialized document and closes the storage.
   --  @param Format Serialization format of the document.
   --  @return An open, Write_Only File_Storage positioned at the implicit
   --  root.
   --  @exception OpenCV_Error Raised when OpenCV cannot open the storage.
   function Create_Memory (Format : Storage_Format) return File_Storage;

   --  Opens Text as a Read_Only memory-backed File_Storage. OpenCV
   --  4.10 auto-detects XML, YAML, or JSON from the contents. Raises
   --  OpenCV_Error if Text is empty, contains an embedded NUL, or
   --  cannot be parsed.
   --  @param Text A previously serialized document.
   --  @return An open, Read_Only File_Storage positioned at the implicit
   --  root.
   --  @exception OpenCV_Error Raised when Text is empty, contains an
   --  embedded NUL, or cannot be parsed.
   function Open_Memory (Text : String) return File_Storage;

   --  Finalizes an open memory Write_Only File_Storage, releases the
   --  OpenCV writer, and returns the complete serialized document.
   --  Self becomes closed on a successful first finish even if a later
   --  Ada conversion fails. Subsequent Write, Read, and
   --  Close_And_Get_Text calls raise OpenCV_Error. Disk storage,
   --  memory readers, and writers with unclosed structures raise
   --  OpenCV_Error. An unbalanced Close_And_Get_Text does not close
   --  the writer. The returned String does not
   --  depend on Self.
   --  @param Self The memory-backed Write_Only storage to finish.
   --  @return The complete serialized document.
   --  @exception OpenCV_Error Raised for disk storage, a reader, a closed
   --  storage, or a writer with unclosed structures.
   function Close_And_Get_Text (Self : in out File_Storage) return String;

   --  Writes Value under Name. Self must be an open Write_Only storage.
   --  Value is borrowed and is not modified. Empty and non-contiguous
   --  Mats are accepted. Raises OpenCV_Error if Self is not open for
   --  writing or if Name is empty or contains an embedded NUL.
   --  @param Self The open Write_Only storage.
   --  @param Name Nonempty, NUL-free name of the node, in the current root
   --  or mapping.
   --  @param Value The Mat to persist.
   --  @exception OpenCV_Error Raised when Self is not open for writing, the
   --  current context is a sequence, or Name is empty or contains an
   --  embedded NUL.
   procedure Write (Self : in out File_Storage; Name : String; Value : Mat);

   --  Writes Value as an OpenCV signed 32-bit integer node. With
   --  OpenCV 4.10, Value must be in -2_147_483_647 .. 2_147_483_647
   --  because OpenCV formats integers with abs(int). Raises
   --  OpenCV_Error if Value is outside that write domain, if Self is
   --  not open for writing, or if Name is empty or contains an
   --  embedded NUL.
   --  @param Self The open Write_Only storage.
   --  @param Name Nonempty, NUL-free name of the node, in the current root
   --  or mapping.
   --  @param Value The integer to persist, in -2_147_483_647 ..
   --  2_147_483_647.
   --  @exception OpenCV_Error Raised when Value is outside the write domain,
   --  Self is not open for writing, the current context is a sequence, or
   --  Name is empty or contains an embedded NUL.
   procedure Write
     (Self : in out File_Storage; Name : String; Value : Integer);

   --  Writes Value as an OpenCV double node. Raises OpenCV_Error if
   --  Self is not open for writing or if Name is empty or contains an
   --  embedded NUL.
   --  @param Self The open Write_Only storage.
   --  @param Name Nonempty, NUL-free name of the node, in the current root
   --  or mapping.
   --  @param Value The real number to persist.
   --  @exception OpenCV_Error Raised when Self is not open for writing, the
   --  current context is a sequence, or Name is empty or contains an
   --  embedded NUL.
   procedure Write
     (Self : in out File_Storage; Name : String; Value : Long_Float);

   --  Writes Value as an OpenCV string node. Raises OpenCV_Error if
   --  Value contains an embedded NUL, if Self is not open for writing,
   --  or if Name is empty or contains an embedded NUL.
   --  @param Self The open Write_Only storage.
   --  @param Name Nonempty, NUL-free name of the node, in the current root
   --  or mapping.
   --  @param Value The NUL-free string to persist; it may be empty.
   --  @exception OpenCV_Error Raised when Value or Name contains an embedded
   --  NUL, Self is not open for writing, the current context is a sequence,
   --  or Name is empty.
   procedure Write (Self : in out File_Storage; Name : String; Value : String);

   --  Starts a named mapping child of the current root or mapping.
   --  Raises OpenCV_Error if Self is not open for writing, if Name is
   --  empty or contains an embedded NUL, or if the current write
   --  context is a sequence. Close it with End_Structure.
   --  @param Self The open Write_Only storage.
   --  @param Name Nonempty, NUL-free name of the new mapping.
   --  @exception OpenCV_Error Raised when Self is not open for writing,
   --  Name is empty or contains an embedded NUL, or the current context is a
   --  sequence.
   procedure Begin_Map (Self : in out File_Storage; Name : String);

   --  Starts an unnamed mapping element of the current sequence.
   --  Raises OpenCV_Error if Self is not open for writing or if the
   --  current write context is not a sequence. Close it with End_Structure.
   --  @param Self The open Write_Only storage.
   --  @exception OpenCV_Error Raised when Self is not open for writing or
   --  the current context is not a sequence.
   procedure Begin_Map (Self : in out File_Storage);

   --  Starts a named sequence child of the current root or mapping.
   --  Raises OpenCV_Error if Self is not open for writing, if Name is
   --  empty or contains an embedded NUL, or if the current write
   --  context is a sequence. Close it with End_Structure.
   --  @param Self The open Write_Only storage.
   --  @param Name Nonempty, NUL-free name of the new sequence.
   --  @exception OpenCV_Error Raised when Self is not open for writing,
   --  Name is empty or contains an embedded NUL, or the current context is a
   --  sequence.
   procedure Begin_Sequence (Self : in out File_Storage; Name : String);

   --  Starts an unnamed sequence element of the current sequence.
   --  Raises OpenCV_Error if Self is not open for writing or if the
   --  current write context is not a sequence. Close it with End_Structure.
   --  @param Self The open Write_Only storage.
   --  @exception OpenCV_Error Raised when Self is not open for writing or
   --  the current context is not a sequence.
   procedure Begin_Sequence (Self : in out File_Storage);

   --  Ends the current mapping or sequence opened by Begin_Map or
   --  Begin_Sequence. The implicit root cannot be closed.
   --  @param Self The open Write_Only storage.
   --  @exception OpenCV_Error Raised when Self is not open for writing or
   --  no structure is open.
   procedure End_Structure (Self : in out File_Storage);

   --  Appends Value as the next element of the current sequence.
   --  Valid only while the current write context is a sequence. Empty and
   --  non-contiguous Mats are accepted.
   --  @param Self The open Write_Only storage.
   --  @param Value The Mat to append.
   --  @exception OpenCV_Error Raised when Self is not open for writing or
   --  the current context is not a sequence.
   procedure Append (Self : in out File_Storage; Value : Mat);

   --  Appends Value as the next element of the current sequence, as an
   --  OpenCV signed 32-bit integer node. Valid only while the current write
   --  context is a sequence. The write domain of the named Write for Integer
   --  applies.
   --  @param Self The open Write_Only storage.
   --  @param Value The integer to append, in -2_147_483_647 ..
   --  2_147_483_647.
   --  @exception OpenCV_Error Raised when Value is outside the write domain,
   --  Self is not open for writing, or the current context is not a
   --  sequence.
   procedure Append (Self : in out File_Storage; Value : Integer);

   --  Appends Value as the next element of the current sequence, as an
   --  OpenCV double node. Valid only while the current write context is a
   --  sequence.
   --  @param Self The open Write_Only storage.
   --  @param Value The real number to append.
   --  @exception OpenCV_Error Raised when Self is not open for writing or
   --  the current context is not a sequence.
   procedure Append (Self : in out File_Storage; Value : Long_Float);

   --  Appends Value as a string sequence element. Raises OpenCV_Error
   --  if Value contains an embedded NUL.
   --  @param Self The open Write_Only storage.
   --  @param Value The NUL-free string to append; it may be empty.
   --  @exception OpenCV_Error Raised when Value contains an embedded NUL,
   --  Self is not open for writing, or the current context is not a
   --  sequence.
   procedure Append (Self : in out File_Storage; Value : String);

   --  Enters the named mapping child of the current root or mapping.
   --  A missing name or a non-mapping node raises OpenCV_Error. Leave it
   --  with Leave_Structure.
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the mapping.
   --  @exception OpenCV_Error Raised when the name is missing, the node is
   --  not a mapping, or the current context is a sequence.
   procedure Enter_Map (Self : in out File_Storage; Name : String);

   --  Enters the indexed mapping child of the current sequence.
   --  Index is zero-based. Valid only inside a sequence. Leave it with
   --  Leave_Structure.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @exception OpenCV_Error Raised when the current context is not a
   --  sequence, Index is out of range, or the node is not a mapping.
   procedure Enter_Map (Self : in out File_Storage; Index : Natural);

   --  Enters the named sequence child of the current root or mapping.
   --  A missing name or a non-sequence node raises OpenCV_Error. Leave it
   --  with Leave_Structure.
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the sequence.
   --  @exception OpenCV_Error Raised when the name is missing, the node is
   --  not a sequence, or the current context is a sequence.
   procedure Enter_Sequence (Self : in out File_Storage; Name : String);

   --  Enters the indexed sequence child of the current sequence.
   --  Index is zero-based. Valid only inside a sequence. Leave it with
   --  Leave_Structure.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @exception OpenCV_Error Raised when the current context is not a
   --  sequence, Index is out of range, or the node is not a sequence.
   procedure Enter_Sequence (Self : in out File_Storage; Index : Natural);

   --  Returns to the parent read context. The implicit root cannot be
   --  left.
   --  @param Self The open Read_Only storage.
   --  @exception OpenCV_Error Raised when the current context is the
   --  implicit root.
   procedure Leave_Structure (Self : in out File_Storage);

   --  Returns FileNode::size of the current sequence. Valid only
   --  while the current read context is a sequence.
   --  @param Self The open Read_Only storage.
   --  @return The number of elements of the current sequence.
   --  @exception OpenCV_Error Raised when the current context is not a
   --  sequence.
   function Sequence_Length (Self : File_Storage) return Natural;

   --  Counts entries at the implicit root (stream 0) or in the entered
   --  mapping. A current mapping with no entries has length zero. Self
   --  must be open Read_Only; a sequence context raises OpenCV_Error.
   --  Navigation is unchanged.
   --  @param Self The open Read_Only storage.
   --  @return The number of entries of the current root or mapping.
   --  @exception OpenCV_Error Raised when Self is not open for reading or
   --  the current context is a sequence.
   function Map_Length (Self : File_Storage) return Natural;

   --  Returns the zero-based Index key in OpenCV's FileNode mapping
   --  iteration order (not sorted). The String is independently owned.
   --  Requires open Read_Only storage and Index < Map_Length (Self);
   --  a sequence context or out-of-range index raises OpenCV_Error.
   --  Navigation is unchanged.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in iteration order.
   --  @return The name of that entry.
   --  @exception OpenCV_Error Raised when Self is not open for reading, the
   --  context is a sequence, or Index is out of range.
   function Map_Key (Self : File_Storage; Index : Natural) return String;

   --  Observe an existing named child at the root or in an entered mapping.
   --  Requires open Read_Only storage and a nonempty, NUL-free name.
   --  Missing names and sequence contexts raise OpenCV_Error. Navigation
   --  is unchanged; serialized Mats report Mapping_Node.
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the child.
   --  @return The structural category of the child.
   --  @exception OpenCV_Error Raised when Self is not open for reading, the
   --  name is missing or invalid, or the context is a sequence.
   function Kind (Self : File_Storage; Name : String) return Node_Kind;

   --  Observe a zero-based child of the entered sequence. Requires open
   --  Read_Only storage; root/map contexts and out-of-range indices raise
   --  OpenCV_Error. Navigation is unchanged.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @return The structural category of the child.
   --  @exception OpenCV_Error Raised when Self is not open for reading, the
   --  context is not a sequence, or Index is out of range.
   function Kind (Self : File_Storage; Index : Natural) return Node_Kind;

   --  Reads the named Mat. Self must be an open Read_Only storage. The
   --  result owns independent storage and does not depend on Self.
   --  A missing name raises OpenCV_Error. A present empty Mat returns
   --  an empty Mat. A node that cannot be converted to Mat raises
   --  OpenCV_Error.
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the node.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the name is missing, the node
   --  cannot be converted to a Mat, or Self is not open for reading.
   function Read_Mat (Self : File_Storage; Name : String) return Mat;

   --  Reads the named signed 32-bit integer node. A real, string, Mat,
   --  or missing node raises OpenCV_Error. The exact stored integer is
   --  returned.
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the node.
   --  @return The stored integer.
   --  @exception OpenCV_Error Raised when the node is missing or is not an
   --  integer node.
   function Read_Integer (Self : File_Storage; Name : String) return Integer;

   --  Reads the named real node, or widens a named integer node to
   --  Long_Float. A string, Mat, or missing node raises OpenCV_Error.
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the node.
   --  @return The stored real number, or the widened integer.
   --  @exception OpenCV_Error Raised when the node is missing or is neither
   --  a real nor an integer node.
   function Read_Real (Self : File_Storage; Name : String) return Long_Float;

   --  Reads the named string node. Numeric, Mat, and missing nodes
   --  raise OpenCV_Error. An actually stored empty string is returned
   --  as "".
   --  @param Self The open Read_Only storage.
   --  @param Name Nonempty, NUL-free name of the node.
   --  @return The stored string, as an independently owned String.
   --  @exception OpenCV_Error Raised when the node is missing or is not a
   --  string node.
   function Read_String (Self : File_Storage; Name : String) return String;

   --  Reads the indexed current-sequence Mat. Index is zero-based.
   --  Valid only while the current read context is a sequence.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @return A new Mat with independent storage.
   --  @exception OpenCV_Error Raised when the context is not a sequence,
   --  Index is out of range, or the node cannot be converted to a Mat.
   function Read_Mat (Self : File_Storage; Index : Natural) return Mat;

   --  Reads the indexed current-sequence integer node. Index is
   --  zero-based. A real, string, Mat, or missing node raises
   --  OpenCV_Error.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @return The stored integer.
   --  @exception OpenCV_Error Raised when the context is not a sequence,
   --  Index is out of range, or the node is not an integer node.
   function Read_Integer (Self : File_Storage; Index : Natural) return Integer;

   --  Reads the indexed current-sequence real node, or widens an
   --  indexed integer node to Long_Float.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @return The stored real number, or the widened integer.
   --  @exception OpenCV_Error Raised when the context is not a sequence,
   --  Index is out of range, or the node is neither a real nor an integer
   --  node.
   function Read_Real (Self : File_Storage; Index : Natural) return Long_Float;

   --  Reads the indexed current-sequence string node. Numeric, Mat,
   --  and missing nodes raise OpenCV_Error.
   --  @param Self The open Read_Only storage.
   --  @param Index Zero-based position in the current sequence.
   --  @return The stored string, as an independently owned String.
   --  @exception OpenCV_Error Raised when the context is not a sequence,
   --  Index is out of range, or the node is not a string node.
   function Read_String (Self : File_Storage; Index : Natural) return String;

private

   type Storage_Backend is (Disk, Memory);

   type File_Storage is new Ada.Finalization.Limited_Controlled with record
      Handle  : OpenCV.Internal.C_API.File_Storage_Handle :=
        OpenCV.Internal.C_API.Null_File_Storage_Handle;
      Mode    : Storage_Mode := Read_Only;
      Backend : Storage_Backend := Disk;
      Opened  : Boolean := False;
   end record;

   --  Controlled finalization: closes and releases the native FileStorage
   --  owned by Self. A disk writer is completed when it is closed. Closing
   --  an already closed storage is harmless.
   --  @param Self The File_Storage being finalized.
   overriding
   procedure Finalize (Self : in out File_Storage);

end OpenCV.Core.Persistence;
