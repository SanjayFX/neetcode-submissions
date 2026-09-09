import math, sys
import boundary_kml as bk

def exact_quad(lat1, lat2, lon1, lon2):
    """Exact WGS84 ellipsoidal area of a geographic quadrangle."""
    dl = math.radians(lon2 - lon1)
    return dl * (bk.A**2 / 2.0) * (bk._q(math.radians(lat2)) - bk._q(math.radians(lat1)))

ok = True

# --- 0. total ellipsoid surface area sanity check
tot = exact_quad(-90, 90, 0, 360)
ref = 5.100656217240886e14
print(f"[0] ellipsoid surface  {tot:.6e} vs {ref:.6e}  dev {abs(tot-ref)/ref*100:.6f}%")
ok &= abs(tot-ref)/ref < 1e-9

# --- 1. LAEA vs exact, on a quadrangle the size of the assumed site, near Anantapur
for (la1,la2,lo1,lo2,label) in [
    (14.60,14.90,77.30,77.65,"~ site sized (35x33 km)"),
    (14.00,15.00,77.00,78.00,"1 deg x 1 deg"),
    (14.700,14.705,77.500,77.506,"tiny (0.5 x 0.6 km)"),
]:
    N=400
    ring=[]
    for i in range(N): ring.append((la1, lo1+(lo2-lo1)*i/N))
    for i in range(N): ring.append((la1+(la2-la1)*i/N, lo2))
    for i in range(N): ring.append((la2, lo2-(lo2-lo1)*i/N))
    for i in range(N): ring.append((la2-(la2-la1)*i/N, lo1))
    lat0=sum(p[0] for p in ring)/len(ring); lon0=sum(p[1] for p in ring)/len(ring)
    got = bk.ellipsoidal_area(ring, lat0, lon0)
    exp = exact_quad(la1,la2,lo1,lo2)
    dev = abs(got-exp)/exp*100
    print(f"[1] LAEA {label:24s} {got/1e6:11.5f} km2  exact {exp/1e6:11.5f}  dev {dev:.7f}%")
    ok &= dev < 1e-4

    sph = bk.spherical_excess_area(ring)
    sdev = abs(sph-exp)/exp*100
    print(f"    spherical-excess crosscheck        {sph/1e6:11.5f} km2  dev {sdev:.6f}%")
    ok &= sdev < 0.01

# --- 2. Vincenty against known geodesic distances
for (a,b,c,d,exp,label) in [
    (0,0,0,1,111319.4907932736,"1 deg lon at equator"),
    (14.6,77.3,14.9,77.3,33193.8875,"0.3 deg lat arc"),
]:
    got=bk.vincenty(a,b,c,d); dev=abs(got-exp)/exp*100
    print(f"[2] vincenty {label:22s} {got:12.3f} m  ref {exp:12.3f}  dev {dev:.4f}%")
    ok &= dev < 0.05

# --- 3. area is invariant to vertex winding order and to projection origin
sq=[(14.60,77.30),(14.60,77.65),(14.90,77.65),(14.90,77.30)]
a1=bk.ellipsoidal_area(sq,14.75,77.475)
a2=bk.ellipsoidal_area(list(reversed(sq)),14.75,77.475)
a3=bk.ellipsoidal_area(sq, 20.0, 60.0)   # deliberately far-off origin
print(f"[3] winding invariance   {abs(a1-a2)/a1*100:.10f}%   far-origin drift {abs(a1-a3)/a1*100:.7f}%")
ok &= abs(a1-a2)/a1 < 1e-12 and abs(a1-a3)/a1 < 1e-6

print("\nRESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
