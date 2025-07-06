Home » Data Access » Open Data » Ocean » Global Ocean Surface Current

# Global Ocean Surface Current

![Global Ocean Surface Current](https://mosdac.gov.in/sites/default/files/styles/medium/public/field/image/world_circulation-1.jpg?itok=dCbexBpU)
The Global Ocean Surface Current defined here as the average current for the top 0 to 30m layer is derived from the synergistic use of three different satellite derived parameters. The first one is the Altimeter derived gridded Map of Absolute Dynamic Topography (MADT) generated from the suite of altimeters such as JASON-2, SARAL/ALTIKA, Cryosat etc., the second data set is the gridded ocean surface vector winds derived ASCAT wind data and the last one is the gridded SST data derived from AVHRR. The methodology presented by Bonjean and Lagerloef, (2002) is used to derive ocean surface current by combining the geostrophic component from altimeter data and the ageostrophic component from scatterometer and radiometer data. The method of deriving the surface current is based on the resolution of quasi-steady quasi-linear momentum equations, neglecting local acceleration. Equatorial velocities are obtained by solving a weak formulation of the momentum equations using a basis set of orthogonal polynomials.

### Data Access

Click Here to access the Science Products . Request to use MOSDAC Single Sign On user credentials to download the data.

### Data Version

- Version 1.0 (beta)

### Data Sources

    1. The daily gridded map of Absolute Dynamic Topography data is obtained from

      1. AVISO/DUACS ftp site (ftp://ftp.aviso.oceanobs.com)


    1. The daily gridded ocean surface vector wind data from ASCAT is obtained from

      1. ftp://ftp.ifremer.fr/ifremer/cersat/products/gridded/MWF/L3/ASCAT/Daily


    1. The daily gridded SST data of Reynolds OISST is obtained from

      1. ftp://eclipse.ncdc.noaa.gov/pub/OI-daily-v2/NetCDF

### Data Citation

- This dataset may be cited as "MOSDAC (http://www.mosdac.gov.in)",(Sikhakolli et al., 2013). Sikhakolli, R., R. Sharma, R. Kumar, B. S. Gohil, A. Sarkar, K. V. S. R. Prasad and S. Basu, Improved determination of Indian Ocean surface currents using satellite data, Rem. Sens. Lett., 4, 335-343, 2013.

### Processing Steps

1. Using the daily gridded data of MADT, Vector winds and SST data the Geostrophic, wind driven and buoyancy components of the ocean surface current respectively are first calculated for the off-equatorial regions (3°N to 90°N and 3°S to 90°S).
2. Using the polynomial expansion the equatorial currents (±3° latitude band) are derived.
3. The daily ocean surface current at 0.25° resolution is then derived by applying a linear weighted average procedure to the equatorial and off equatorial current solutions with in the latitude band of ± 3° to ± 4° band.

### References

1. Bentamy A..; D. Croize-Fillon, 2011: Gridded surface wind fields from Metop/ASCAT measurements. Inter. Journal of Remote Sensing. DOI 10.1080/01431161.2011.600348.
2. Bonjean, F, and G. S. E. Lagerloef (2002), Diagnostic model and analysis of the surface currents in the tropical Pacific Ocean., J. Phys. Oceanogr., 32, 2938-2954.
3. Reynolds, R. W., T. M. Smith,\_C. Liu, D. B. Chelton, K. S. Casey, and M. G. Schlax (2007), Daily high-resolution-blended analyses for sea surface temperature, J. Climate., 20, 5473-5496.
4. Sikhakolli, R., R. Sharma, S. Basu, B. S. Gohil, A. Sarkar and K. V. S. Prasad, Evaluation of OSCAR ocean surface current product in the tropical Indian Ocean using in situ data , J. Earth Syst. Sci., 2013.
5. Sikhakolli, R., R. Sharma, R. Kumar, B. S. Gohil, A. Sarkar, K. V. S. R. Prasad and S. Basu, Improved determination of Indian Ocean surface currents using satellite data, Rem. Sens. Lett., 4, 335-343, 2013.
6. SSALTO/DUACS user hand book: (M)SLA and (M)ADT Near Real Time and Delayed Time products, AVISO, Nov 2009.

### Derivation Techniques and Algorithm

    * The methodology follows the work of Bonjean and Lagerloef (2002). The basic equations are those of quasi linear and steady flow in a surface layer where the horizontal velocity U = (u,v) is allowed to vary with vertical coordinate _z_ , and where vertical turbulent mixing is characterized by an eddy viscosity _A_ uniform with depth. The vertical shear Uz reaches zero at a constant scaling depth _z_ = - _H_. Using complex notations _U(x,y,z,t) = u + iv and ∇ = ∂/∂x + i ∂/∂y_ , the basic equations are

|  
---|---  
_if_ U = - (1/ρm) ∇ p + AUz | (1a)  
(1/ρm) pz = -g + ∇θ | (1b)  
∇θ = g χT ∇SST , | (1c)  
|  
 _ with - H ≤ z ≤ 0, and subject to the following boundary conditions  
|  
---|---  
Uz (z=0) = τ / A | (2a)  
Uz (z = -H) = 0 | (2b)  
|  
 _ The characteristic density is ρm = 1025 kg m -3,
_ The acceleration due to gravity g = 9.8 m s-2,
_ and the coefficient of thermal expansion χT = 3 x 10-4 K-1,
_ The vector field τ = τx + i τ y represents the surface wind stress divided by ρm,
_ H has been chosen to be 70 m,
_ The parameter A is chosen by the empirical formulation as A = a (|W|/W1)b | w| 1 m s-1 where W1 = 1 m s-1 , a = 8 x 10-5 m 2 s-1 , and b = 2.2
_ where W1 = 1 m s-1 , a = 8 x 10-5 m 2 s-1 , and b = 2.2 . \* The equation for the velocity shear is

|  
---|---  
Uz - (if/A) Uz = (1/A)∇θ | (3)  
|  
 \* which is a second-order differential equation in velocity shear Uz , subject to the boundary conditions (2a,b). After solving for the shear profiles, one can find an expression for the velocity at the surface, which is

|  
---|---  
_if_ U0= -g ∇ζ + (1/H ) q(H/he)τ + ((H/2)/q(H/2he))∇θ | (4)  
|

- Here the function q is defined by q (x) = x /tanh (x) and he = (A/if )1/2 is complex and its modulus is proportional to the Ekman depth he = sqrt( 2A/|f|).
- Using equation (4) and the datasets mentioned above, the daily ocean surface currents were generated. Equatorial velocities (±3° latitude band) are obtained by solving a weak formulation of the momentum equations using a basis set of orthogonal polynomials as described in Bonjean and Lagerloef (2002).

### Limitations

- As the equatorial currents are estimated through an approximation procedure using polynomial coefficients the correlation with in-situ currents in the equatorial region is observed to be relatively poorer especially for the meridional currents.

### Known problems with data

- As these input satellite data are not very reliable near to the coast, the estimated currents very near to the coast may also have problems.

### Related data collections

1. OSCAR Currents: Bonjean, F, and G. S. E. Lagerloef (2002), Diagnostic model and analysis of the surface currents in the tropical Pacific Ocean., J. Phys. Oceanogr., 32, 2938-2954
2. GEKCO Currents: Joel Sudre, Christophe Maes and Veronique Garcon (2013), On the global estimates of geostrophic and Ekman surface currents. Limnology and Oceanography. DOI: 10.1215/21573689-2071927

### File Naming Convention

- The typical file name is **'ISRO_CURRENT_TOT_YYYYMMDD.nc'** where
-     * **'ISRO_CURRENT'** signifies that this product is generated at SAC-ISRO
  - word **'TOT'** signifies that this is the total current (Geostrophic + ageostrophic)
  - **'YYYY'** corresponds to the year, ex: 2015
  - **'MM'** corresponds to the month, ex: 09
  - **'DD'** corresponds to the date, ex: 26
  - All the data files are in NetCDF 4 format and the images are in gif format

### MetaData

| Sr. No | Core Metadata Elements                                                      | Definition                                                                                                                                                                                                                                                         |
| ------ | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------- |
| 1      | Metadata language                                                           | English                                                                                                                                                                                                                                                            |
| 2      | Metadata Contact                                                            | Dr. Rajesh Sikhakolli, GRD/AOSG/EPSA, Space Applications Centre (ISRO), Ahmedabad-380015, India. Email: srajesh@sac.isro.gov.in                                                                                                                                    |
| 3      | Metadata date                                                               | September 15, 2015                                                                                                                                                                                                                                                 |
| 4      | Data Lineage or Quality                                                     | Daily ocean surface currents derived from satellite data                                                                                                                                                                                                           |
| 5      | Title                                                                       | Zonal and Meridional components of Ocean Surface Current (m/s)                                                                                                                                                                                                     |
| 6      | Abstract                                                                    | Daily ocean surface currents(m/s) derived from the synergistic use of satellite derived Sea Level, Ocean surface vector winds and Sea surface temperature data.                                                                                                    |
| 7      | Dataset Contact                                                             | Dr. Rajesh Sikhakolli, GRD/AOSG/EPSA, Space Applications Centre (ISRO), Ahmedabad-380015, India. Email: srajesh@sac.isro.gov.in                                                                                                                                    |
| 8      | Update frequency                                                            | Daily                                                                                                                                                                                                                                                              |
| 9      | Access Rights or Restriction                                                | Open Access                                                                                                                                                                                                                                                        |
| 10     | Spatial Resolution                                                          | 0.25° deg (or) ~25km                                                                                                                                                                                                                                               |
| 11     | Language                                                                    | English                                                                                                                                                                                                                                                            |
| 12     | Topic Category                                                              | Physical Oceanography                                                                                                                                                                                                                                              |
| 13     | Keywords                                                                    | Ocean Currents, Ocean Circulation                                                                                                                                                                                                                                  |
| 14     | Date or period                                                              | Daily                                                                                                                                                                                                                                                              |
| 15     | Responsible Party                                                           | Dr. Rajesh Sikhakolli, GRD/AOSG/EPSA, Space Applications Centre (ISRO), Ahmedabad-380015, India. Email: srajesh@sac.isro.gov.in                                                                                                                                    |
| 16     | Organization                                                                | Space Applications Centre (ISRO), Ahmedabad, India                                                                                                                                                                                                                 |
| 16a    | Org. role                                                                   | Calculated Ocean Surface currents (m/s) for each day using daily map of absolute dynamic topography (MADT) data from AVISO (SSALTO/DUACS user hand book-2009), gridded wind data from ASCAT (Bentamy et al., 2011) and SST data from AVHRR (Reynolds et al., 2007) |
| 16b    | Individual Name                                                             | Dr. Rajesh Sikhakolli, GRD/AOSG/EPSA, Space Applications Centre (ISRO), Ahmedabad-380015, India. Email: srajesh@sac.isro.gov.in                                                                                                                                    |
| 16c    | Position                                                                    | Scientist/Engineer, GRD/AOSG/EPSA, SAC (ISRO), Ahmedabad-380015, India. Ph: +91 79 2691 6052. Email: srajesh@sac.isro.gov.in                                                                                                                                       |
| 17     | Vertical Extent (minimumValue, maximumValue, unitOfMeasure, vertical datum) | Average ocean surface current for 0 to 30 m vertical layer in m/s                                                                                                                                                                                                  |
| 18     | Geographic Extent                                                           |                                                                                                                                                                                                                                                                    | Latitude Range: -90 to 90 deg |

---

Longitude Range: 0 to 360 deg  
19 | Geographic Name, Geographic Identifier | Global Ocean  
20 | Bounding box | | Latitude Range: -90 to 90 deg

---

Longitude Range: 0 to 360 deg  
21 | Temporal Extent | Daily  
22 | Distribution Information | Online download of data files in NetCDF format and images in GIF format  
23 | Processing Level | Level 4  
24 | Reference System | Projection - Cartesian Co-ordinate System

### Tags:

- Opendata
- Ocean
