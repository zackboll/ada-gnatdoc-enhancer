with OpenCV.Core.Float64_Vec4;

--  Typed access to one complete CV_64FC4 SparseMat element. Components are
--  OpenCV channel indices 0 .. 3; no semantic meaning is assigned.
--  Each operation validates that the matrix is allocated and has exactly this
--  depth and four channels, then validates the coordinates, and raises
--  OpenCV_Error on any mismatch. Coordinates are zero-based, one per
--  dimension. A missing coordinate reads as an all-zero vector but is not the
--  same as a stored all-zero vector. Writes go to the shared nodes, so every
--  shallow alias of the Sparse_Mat observes them.

package OpenCV.Core.Sparse.Float64_Vec4_Access is

   --  Missing nodes read as an all-zero vector and are not created.
   --  @param Image An allocated Float64 Sparse_Mat with exactly four
   --  channels.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @return The stored vector, or an all-zero vector when no node is
   --  stored there.
   --  @exception OpenCV_Error Raised when Image is unallocated or has another
   --  depth or channel count, Indices does not have exactly Dimension_Count
   --  entries, or an index is out of bounds, or OpenCV reports a failure.
   function Get
     (Image : Sparse_Mat; Indices : Index_Array)
      return OpenCV.Core.Float64_Vec4.Vector;

   --  Inserts the node if absent; an all-zero vector is still stored.
   --  All four channels are stored together.
   --  @param Image An allocated Float64 Sparse_Mat with exactly four
   --  channels.
   --  @param Indices One zero-based index per dimension, each less than the
   --  matching extent.
   --  @param Value The four channel values to store.
   --  @exception OpenCV_Error Raised when Image is unallocated or has another
   --  depth or channel count, Indices does not have exactly Dimension_Count
   --  entries, or an index is out of bounds, or OpenCV reports a failure.
   procedure Set
     (Image   : in out Sparse_Mat;
      Indices : Index_Array;
      Value   : OpenCV.Core.Float64_Vec4.Vector);

   --  Stored nodes only; unspecified order; values are copies.
   --  Do not structurally mutate Image or aliases during callbacks.
   --  Indices have bounds 1 .. Dimension_Count and are zero-based.
   --  @param Image An allocated Float64 Sparse_Mat with exactly four
   --  channels.
   --  @param Process Callback invoked once for each stored node, including
   --  explicitly stored all-zero vectors, with that node's coordinates and
   --  value.
   --  @exception OpenCV_Error Raised before any callback when Image is
   --  unallocated or has another depth or channel count, and also raised if
   --  the native iteration fails, which can happen after earlier callbacks
   --  have already run.
   procedure For_Each_Stored
     (Image   : Sparse_Mat;
      Process :
        not null access procedure
          (Indices : Index_Array; Value : OpenCV.Core.Float64_Vec4.Vector));
end OpenCV.Core.Sparse.Float64_Vec4_Access;
