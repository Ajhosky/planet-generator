# Planet Genesis

Planet Genesis is an interactive procedural planet simulator that combines simplified planetary physics, chemistry, climate modelling and real-time 3D visualization.

The user defines a planet through its chemical composition and orbital parameters. The backend estimates the planet's physical and environmental properties, generates texture maps, and returns the result to a React/Three.js frontend.

## Main features

- Planet generation from chemical composition
- Density, radius, surface gravity and escape velocity estimation
- Equilibrium and surface temperature calculation
- Simplified greenhouse effect
- Atmosphere-retention estimation
- Liquid-water and ocean-coverage estimation
- Internal heating and volcanism estimation
- Habitability, chemistry and stability scores
- Procedural surface, cloud and height maps
- Composition-dependent planet colours
- Atmospheric glow based on methane, ammonia, nitrogen and toxic compounds
- Ring-system generation
- Deterministic moon systems generated from a seed
- Moon orbits, phases, albedo and reflected-light effects
- Debug views for surface, cloud and height maps
- “Why does it look like this?” explanation panel
- Achievement system based on the generated planet
- Asynchronous backend render jobs with progress tracking

## Project structure

The project is split into two repositories:

- Backend: `Ajhosky/planet-generator`
- Frontend: `Ajhosky/planet-generator-fe`

### Backend

Technology:

- Python
- FastAPI
- Pydantic
- NumPy
- Pillow

Important modules:

```text
app/
├── api/
│   └── routes_planet.py
├── jobs/
│   └── planet_jobs.py
├── models/
├── rendering/
│   ├── cache.py
│   ├── fingerprint.py
│   └── texture_generator.py
└── simulation/
    ├── atmosphere.py
    ├── bulk_physics.py
    ├── climate.py
    ├── composition_influence.py
    ├── geology.py
    ├── habitability.py
    ├── hydrosphere.py
    ├── rings.py
    └── simulator.py
```

### Frontend

Technology:

- React
- TypeScript
- Vite
- Three.js
- React Three Fiber
- Drei
- Axios

Important modules:

```text
src/
├── api/
│   └── planetApi.ts
├── components/
│   ├── AchievementsPanel.tsx
│   ├── CompositionPanel.tsx
│   ├── MetricsPanel.tsx
│   ├── OrbitalPanel.tsx
│   ├── WhyPlanetLooksPanel.tsx
│   └── planet/
│       ├── BackendPlanetMaps.tsx
│       ├── MoonSystem.tsx
│       ├── PlanetMesh.tsx
│       ├── PlanetRings.tsx
│       └── PlanetScene.tsx
├── types/
│   └── planet.ts
└── App.tsx
```

## Input parameters

The user controls:

- chemical composition
- mass in Earth masses
- distance from the star in astronomical units
- stellar luminosity relative to the Sun
- planet age in billions of years
- rotation period in hours
- procedural seed
- optional moon system

The chemical composition includes:

- silicates
- iron and magnesium
- water and ice
- carbon
- sulfur
- titanium
- radioactive elements
- nitrogen
- methane
- ammonia
- phosphorus

## Physics model

Planet Genesis is an educational simulator. It uses simplified physically motivated relationships, not a full astrophysical evolution model.

### Density

The average density is estimated as a weighted sum of material densities:

```text
ρ = Σ(fi · ρi)
```

where `fi` is the normalized fraction of a material and `ρi` is its representative density.

### Radius

Radius is estimated from mass and relative density:

```text
R / R⊕ = (M / relative_density)^(1/3)
```

### Surface gravity

```text
g / g⊕ = (M / M⊕) / (R / R⊕)²
```

### Escape velocity

```text
vesc = vesc,Earth · sqrt((M / M⊕) / (R / R⊕))
```

### Planetary temperature

```text
Teq = 278 K · L^(1/4) · (1 - A)^(1/4) / sqrt(d)
```

where `L` is stellar luminosity relative to the Sun, `A` is albedo and `d` is distance in AU.

The final surface temperature also includes greenhouse heating and internal heating.

### Albedo

Albedo is estimated from composition. Water and ice increase reflectivity more strongly than dark carbon-rich or iron-rich terrain.

### Greenhouse effect

The greenhouse approximation depends mainly on methane, ammonia, carbon, nitrogen and the atmosphere score.

### Atmosphere retention

The atmosphere score combines volatile compounds, nitrogen, water inventory, volcanic outgassing, gravity, escape velocity and temperature.

### Internal heat and volcanism

Internal heating depends on radioactive elements, iron and magnesium, planet mass and planet age. Younger, massive and radioactive planets are more likely to remain geologically active.

### Liquid water

Liquid-water stability depends on surface temperature, atmosphere score and water inventory. The simulator distinguishes frozen, liquid and vapor-dominated conditions.

### Habitability

The habitability result combines temperature, ocean coverage, atmosphere, chemistry and environmental stability. The score is comparative and educational.

## How planet colours are determined

The visual appearance is computed from a composition influence map.

| Parameter | Main visual effect |
|---|---|
| Iron and magnesium | dark basalt, metallic and rusty regions |
| Silicates | rocky crust and stronger relief |
| Water and ice | blue oceans or bright frozen regions |
| Carbon | darker charcoal-like terrain |
| Sulfur | yellow and brown deposits |
| Titanium | brighter mineral highlights |
| Radioactive elements | stronger volcanism and lava-like hot spots |
| Methane | orange-brown atmospheric haze |
| Ammonia | pale, milky cloud layers |
| Nitrogen | more stable blue atmospheric glow |
| Phosphorus + water + carbon + nitrogen | increased biological-colour potential |

The procedural seed controls terrain distribution, while the chemical composition controls the strength and type of visual effects.

## Texture generation

For each planet the backend generates:

- `surface_map.png`
- `cloud_map.png`
- `height_map.png`

The height map is used as a displacement and bump map in Three.js. The cloud map is rendered on a slightly larger transparent sphere.

## Rings

The ring model considers available icy, dusty and rocky material, planet mass, gravity, temperature, age, rotation and approximate Roche-limit conditions.

## Moon Physics 2.0

Moon systems are deterministic: the same seed and moon count produce the same system.

Each moon can have generated radius, orbital distance, orbital speed, inclination, initial phase, rotation speed, surface texture, albedo, roughness and a deterministic name.

The visual model also includes orbit paths, illumination from the star, visible lunar phases, a darker night side and limited reflected light.

The moon simulation is physically motivated but is not a full N-body gravitational simulation.

## API workflow

Planet generation uses asynchronous jobs.

```http
POST /api/planet/jobs
GET /api/planet/jobs/{job_id}
```

Possible states:

- `queued`
- `running`
- `succeeded`
- `failed`

## Running the backend

```bash
cd planet-generator
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

## Running the frontend

```bash
cd planet-generator-fe
npm install
npm run dev
```

## Validation

Backend:

```bash
python3 -m compileall app
```

Frontend:

```bash
npm run build
npm run lint
```

## Limitations

- The model uses simplified approximations.
- Composition values are abstract fractions, not a full geochemical equilibrium.
- Atmospheric pressure is represented by a score rather than a complete fluid model.
- Plate tectonics, magnetic fields and atmospheric escape are not simulated over geological time.
- Moon motion is not calculated with a full N-body solver.
- Visual colours are physically motivated approximations, not spectral radiative-transfer results.

## Future development

- axial tilt and seasons
- tidal locking
- magnetic-field estimation
- atmospheric pressure in pascals
- stellar spectral classes
- orbital stability analysis
- atmospheric escape over time
- multi-planet comparison mode
- exportable planet report
- saved generation history
