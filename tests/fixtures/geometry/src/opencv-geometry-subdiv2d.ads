with OpenCV.Geometry;
package OpenCV.Geometry.Subdiv2D is
   type Subdivision is tagged limited private;
   function Locate (Point : OpenCV.Geometry.Point_2D) return Subdivision;
end OpenCV.Geometry.Subdiv2D;
