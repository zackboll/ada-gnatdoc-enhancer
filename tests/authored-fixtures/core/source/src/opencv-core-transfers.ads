--  Explicit independent copies between Mat and UMat. Each operation makes
--  an independent copy: no storage, header or native handle is shared
--  between the source and the result, and later changes to one do not affect
--  the other. These non-primitive operations live in a child package because
--  Ada cannot dispatch simultaneously on Mat and UMat.

package OpenCV.Core.Transfers is

   --  Copies the elements of Self into a newly allocated UMat. The result
   --  owns its own UMat storage and does not share data with Self. Whether
   --  OpenCL is used for the resulting UMat is a native decision and is not
   --  guaranteed.
   --  @param Self The Mat to copy.
   --  @return A new UMat holding a copy of Self's elements.
   --  @exception OpenCV_Error Raised when the native copy fails.
   function To_UMat (Self : Mat) return UMat;

   --  Copies the elements of Self into a newly allocated host Mat. The
   --  result owns its own storage and does not share data with Self.
   --  @param Self The UMat to copy.
   --  @return A new Mat holding a copy of Self's elements.
   --  @exception OpenCV_Error Raised when the native copy fails.
   function To_Mat (Self : UMat) return Mat;
end OpenCV.Core.Transfers;
