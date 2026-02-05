ENV["JULIA_SSL_CA_ROOTS_PATH"] = ""
ENV["JULIA_PKG_SERVER_REGISTRY_PREFERENCE"] = "eager"
import Pkg
Pkg.Registry.update()
Pkg.Registry.add("General")
Pkg.Registry.add(Pkg.RegistrySpec(url="https://github.com/NatLabRockies/JuliaRegistry.git"))
Pkg.instantiate()

Pkg.add("Random123")

# Make sure PRAS installation worked
import PRAS

# Make sure TimeZones works
import TimeZones
# TimeZones.build()
TimeZones.ZonedDateTime(2007, 01, 01, 00, TimeZones.tz"UTC")
