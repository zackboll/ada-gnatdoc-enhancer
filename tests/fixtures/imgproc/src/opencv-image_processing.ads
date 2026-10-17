package OpenCV.Image_Processing is
   type Threshold_Mode is (Binary, Binary_Inverted);
   function Apply_Threshold (Source : Threshold_Mode) return Threshold_Mode;
   function Match_Template (Source : Threshold_Mode) return Threshold_Mode;
   function Match_Template (Source : Threshold_Mode; Scale : Natural) return Threshold_Mode;
end OpenCV.Image_Processing;
