with AMS.MEL.Status;
package AMS.MEL.IR.Image is
type Quaternion is record
      X, Y, Z, W : Long_Float;
   end record;
type Directional is record
      X, Y, Z : Long_Float;
   end record;
type Nav_Error is record
      X, Y, Z, W : Long_Float;
   end record;
type Uncertainty is record
      Sensor_Uncertainties, Platform_Uncertainties : Interfaces.Unsigned_32;
   end record;
type Orientation_Kind is (Euler_Orientation, Quaternion_Orientation);
type Orientation (Kind : Orientation_Kind := Euler_Orientation) is record
      case Kind is
         when Euler_Orientation =>
            Euler_Value : AMS.MEL.Status.Euler;

         when Quaternion_Orientation =>
            Quaternion_Value : Quaternion;
      end case;
   end record;
type Coordinate_System is (LLA, ECEF, NED_Platform, NED_Sensor);
type Sensor_Inertial_State is record
      System_Time_NS                   : Long_Long_Integer;
      Q_XYZW, Q_ECEF_XYZW              : Quaternion;
      Sensor_Position, Sensor_Velocity : Directional;
      Uncertainty                      : Image.Uncertainty;
   end record;
type Sensor_Nav_State is record
      Position, Velocity, Acceleration                   : Directional;
      Position_Error, Velocity_Error, Acceleration_Error : Nav_Error;
      Orientation                                        : Image.Orientation;
      Orientation_Error                                  : Nav_Error;
      Orientation_Velocity                               : Image.Orientation;
      Orientation_Velocity_Error                         : Nav_Error;
      Orientation_Acceleration                           : Image.Orientation;
      Orientation_Acceleration_Error                     : Nav_Error;
      Coordinate_System                                  : Image.Coordinate_System;
   end record;
type Position_Solution_State is (Not_Set, Aligning, Free_Inertial, GPS, Blended);
type North_East_Down is record
      North, East, Down : Long_Float;
   end record;
type Attitude_Rate is record
      Value          : AMS.MEL.Status.Euler;
      System_Time_NS : Long_Long_Integer;
   end record;
type Position_Velocity_Covariance is record
      Position_Position_Pn_Pn : Long_Float;
      Position_Position_Pn_Pe : Long_Float;
      Position_Position_Pn_Pd : Long_Float;
      Position_Position_Pe_Pe : Long_Float;
      Position_Position_Pe_Pd : Long_Float;
      Position_Position_Pd_Pd : Long_Float;
      Position_Velocity_Pn_Vn : Long_Float;
      Position_Velocity_Pn_Ve : Long_Float;
      Position_Velocity_Pn_Vd : Long_Float;
      Position_Velocity_Pe_Ve : Long_Float;
      Position_Velocity_Pe_Vd : Long_Float;
      Position_Velocity_Pd_Vd : Long_Float;
      Velocity_Velocity_Vn_Vn : Long_Float;
      Velocity_Velocity_Vn_Ve : Long_Float;
      Velocity_Velocity_Vn_Vd : Long_Float;
      Velocity_Velocity_Ve_Ve : Long_Float;
      Velocity_Velocity_Ve_Vd : Long_Float;
      Velocity_Velocity_Vd_Vd : Long_Float;
   end record;
type Navigation_Report is record
      System_Time_NS               : Long_Long_Integer;
      State                        : Position_Solution_State;
      Latitude_Rad                 : Long_Float;
      Longitude_Rad                : Long_Float;
      Altitude_M                   : Long_Float;
      Attitude                     : AMS.MEL.Status.Euler;
      Attitude_Rate                : Image.Attitude_Rate;
      Speed                        : North_East_Down;
      Acceleration                 : North_East_Down;
      Wander_Angle_Rad             : Long_Float;
      Magnetic_Heading             : Long_Float;
      Altitude_MSL                 : Long_Float;
      Position_Velocity_Covariance : Image.Position_Velocity_Covariance;
   end record;
end AMS.MEL.IR.Image;
