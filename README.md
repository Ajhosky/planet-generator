# Planet Genesis

Planet Genesis to edukacyjny symulator planetarny, którego celem jest szacowanie podstawowych parametrów planety na podstawie jej składu chemicznego oraz parametrów orbitalnych.

Projekt nie jest pełną symulacją astrofizyczną. Jest to model heurystyczny, czyli uproszczony model obliczeniowy, który korzysta z logicznych zależności między składem planety, masą, odległością od gwiazdy, temperaturą, atmosferą, oceanami i potencjalną przeżywalnością.

Głównym założeniem projektu jest to, że użytkownik podaje skład planety oraz parametry środowiskowe, a aplikacja zwraca oszacowane wartości takie jak:

- gęstość,
- promień,
- grawitacja,
- prędkość ucieczki,
- temperatura równowagowa,
- temperatura powierzchniowa,
- aktywność wulkaniczna,
- siła atmosfery,
- pokrycie oceanami,
- wynik chemii życia,
- stabilność środowiska,
- habitability score,
- klasyfikacja planety,
- ostrzeżenia środowiskowe.

---

## Status projektu

Aktualnie działa backend API oparty o FastAPI.

Dostępny endpoint:

```text
POST /api/planet/simulate
```

Endpoint przyjmuje dane wejściowe planety i zwraca obliczone parametry.

Przykładowe uruchomienie backendu:

```bash
cd backend
uvicorn app.main:app --reload
```

Dokumentacja Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Przykładowe dane wejściowe

```json
{
  "composition": {
    "silicates": 0.35,
    "iron_magnesium": 0.25,
    "water_ice": 0.2,
    "carbon": 0.05,
    "sulfur": 0.03,
    "titanium": 0.02,
    "radioactive_elements": 0.02,
    "nitrogen": 0.03,
    "methane": 0.02,
    "ammonia": 0.02,
    "phosphorus": 0.01
  },
  "mass_earth": 1,
  "distance_au": 1,
  "star_luminosity": 1,
  "age_billion_years": 4.5,
  "rotation_period_hours": 24,
  "planet_type": "regular",
  "seed": 42
}
```

---

## Przykładowy wynik

```json
{
  "parameters": {
    "density_g_cm3": 3.161,
    "radius_earth": 1.203,
    "gravity_g": 0.69,
    "escape_velocity_km_s": 10.197,
    "equilibrium_temperature_k": 258.923,
    "surface_temperature_k": 263.764,
    "surface_temperature_c": -9.386,
    "volcanism_score": 0.035,
    "atmosphere_score": 0.12,
    "ocean_coverage": 0.072,
    "chemistry_score": 0.195,
    "stability_score": 0.4,
    "habitability_score": 35.051
  },
  "classification": "Airless rocky world",
  "warnings": [
    "Atmosphere is probably too thin for surface habitability."
  ]
}
```

---

# Założenia modelu

Model jest uproszczony i służy do generowania realistycznie wyglądających wyników na potrzeby aplikacji edukacyjnej oraz wizualizacyjnej.

Nie symuluje dokładnie:

- pełnej geochemii,
- pełnej dynamiki atmosfery,
- ewolucji gwiazd,
- rzeczywistych równań stanu materii,
- klimatu 3D,
- tektoniki płyt w sensie fizycznym,
- biologii molekularnej.

Zamiast tego model używa heurystyk, czyli przybliżonych zależności:

```text
skład chemiczny + masa + orbita + wiek
→ właściwości fizyczne
→ klimat
→ atmosfera
→ oceany
→ stabilność
→ przeżywalność
```

Dzięki temu projekt jest możliwy do rozwijania, testowania i wizualizacji bez konieczności budowania profesjonalnego silnika astrofizycznego.

---

# Skład planety

Planeta opisywana jest przez zestaw składników:

```text
silicates
iron_magnesium
water_ice
carbon
sulfur
titanium
radioactive_elements
nitrogen
methane
ammonia
phosphorus
```

Wartości wejściowe mogą być podane jako liczby od `0.0` do `1.0`.

Przed obliczeniami skład jest normalizowany, czyli suma wszystkich składników zostaje sprowadzona do `1.0`.

Przykład:

```text
silicates = 0.35
iron_magnesium = 0.25
water_ice = 0.20
```

Po normalizacji każdy składnik oznacza przybliżony udział danego materiału w planecie.

---

# Gęstość planety

## Cel

Gęstość mówi, jak bardzo planeta jest „zbita” i z jak ciężkich materiałów się składa.

Planeta z dużą ilością żelaza i magnezu będzie gęstsza. Planeta z dużą ilością wody, lodu, metanu albo amoniaku będzie mniej gęsta.

## Używany model

Każdemu składnikowi przypisana jest uproszczona gęstość:

```python
MATERIAL_DENSITIES_G_CM3 = {
    "silicates": 3.3,
    "iron_magnesium": 5.2,
    "water_ice": 1.2,
    "carbon": 2.2,
    "sulfur": 2.0,
    "titanium": 4.5,
    "radioactive_elements": 7.0,
    "nitrogen": 0.8,
    "methane": 0.5,
    "ammonia": 0.7,
    "phosphorus": 1.8,
}
```

Następnie liczona jest średnia ważona:

```text
density = suma(udział_składnika × gęstość_składnika)
```

## Dlaczego tak?

To uproszczony odpowiednik liczenia gęstości mieszaniny. W rzeczywistości gęstość planety zależy też od ciśnienia, temperatury, kompresji wnętrza i rozdzielenia na jądro, płaszcz i skorupę.

Na potrzeby aplikacji ten model daje jednak sensowny efekt:

```text
więcej żelaza      → większa gęstość
więcej skał        → średnia gęstość
więcej wody/lodu   → mniejsza gęstość
więcej gazów/lodów → jeszcze mniejsza gęstość
```

---

# Promień planety

## Cel

Promień mówi, jak duża jest planeta w porównaniu do Ziemi.

Wynik podawany jest w jednostkach `R⊕`, czyli promieniach Ziemi.

## Używany model

Model korzysta z zależności między masą, objętością i gęstością.

Podstawowa zależność:

```text
density = mass / volume
```

Dla kuli:

```text
volume ∝ radius³
```

Dlatego:

```text
radius ∝ (mass / density)^(1/3)
```

W kodzie używamy wersji względem Ziemi:

```text
density_relative = density / Earth_density

radius_earth = (mass_earth / density_relative)^(1/3)
```

## Dlaczego tak?

Jeżeli planeta ma masę podobną do Ziemi, ale mniejszą gęstość, musi mieć większy promień.

Przykład:

```text
niska gęstość + masa 1 Ziemi → większa planeta
wysoka gęstość + masa 1 Ziemi → mniejsza planeta
```

To jest dobre uproszczenie dla edukacyjnego modelu planet skalistych i oceanicznych.

---

# Grawitacja powierzchniowa

## Cel

Grawitacja powierzchniowa mówi, jak silnie planeta przyciąga obiekty na swojej powierzchni.

Wynik podawany jest w jednostkach `g`, gdzie `1 g` oznacza grawitację ziemską.

## Używany model

Grawitacja zależy od masy i promienia planety:

```text
gravity = mass / radius²
```

W jednostkach ziemskich:

```text
gravity_g = mass_earth / radius_earth²
```

## Dlaczego tak?

Prawo grawitacji mówi, że większa masa zwiększa przyciąganie, a większy promień oddala powierzchnię od środka masy, więc zmniejsza grawitację.

Grawitacja jest ważna, bo wpływa na:

- zdolność utrzymania atmosfery,
- warunki dla życia,
- ciśnienie powierzchniowe,
- możliwość istnienia oceanów,
- przeżywalność organizmów podobnych do ziemskich.

---

# Prędkość ucieczki

## Cel

Prędkość ucieczki mówi, jak szybko trzeba się poruszać, żeby opuścić pole grawitacyjne planety.

Wynik podawany jest w `km/s`.

## Używany model

Względem Ziemi:

```text
escape_velocity = Earth_escape_velocity × sqrt(mass_earth / radius_earth)
```

Ziemska prędkość ucieczki wynosi w modelu:

```text
11.186 km/s
```

## Dlaczego tak?

Planeta o większej masie trudniej traci atmosferę. Planeta o małej masie i małej prędkości ucieczki może łatwiej utracić lekkie gazy w przestrzeń kosmiczną.

W modelu prędkość ucieczki wpływa na ocenę atmosfery.

---

# Albedo

## Cel

Albedo określa, jaka część światła gwiazdy jest odbijana przez planetę.

Wysokie albedo oznacza, że planeta odbija dużo światła i jest chłodniejsza. Niskie albedo oznacza, że planeta pochłania więcej energii i jest cieplejsza.

## Używany model

Albedo jest szacowane na podstawie składu:

```text
water_ice          → wysokie albedo
silicates          → średnie albedo
iron_magnesium     → niższe albedo
carbon             → niskie albedo
```

Przykład modelu:

```text
albedo =
    water_ice × 0.55
  + silicates × 0.25
  + iron_magnesium × 0.18
  + carbon × 0.10
```

Wartość jest ograniczana do zakresu `0.05 - 0.85`.

## Dlaczego tak?

Lód i jasne powierzchnie odbijają dużo światła, natomiast ciemne skały i materiały bogate w węgiel pochłaniają więcej energii.

Albedo jest potrzebne do obliczenia temperatury równowagowej.

---

# Temperatura równowagowa

## Cel

Temperatura równowagowa to przybliżona temperatura planety bez pełnego uwzględnienia złożonego efektu cieplarnianego.

Zależy głównie od:

- odległości od gwiazdy,
- jasności gwiazdy,
- albedo planety.

## Używany model

```text
T_eq = 278 × luminosity^0.25 × (1 - albedo)^0.25 / sqrt(distance_au)
```

Gdzie:

```text
T_eq            → temperatura równowagowa w kelwinach
luminosity      → jasność gwiazdy względem Słońca
distance_au     → odległość od gwiazdy w AU
albedo          → odbijalność planety
```

## Dlaczego tak?

Energia otrzymywana od gwiazdy maleje z kwadratem odległości, dlatego temperatura zmienia się w przybliżeniu z pierwiastkiem od odległości.

Zależność od jasności i albedo jest potęgowana przez `0.25`, ponieważ temperatura promieniującego ciała zależy od czwartej potęgi energii promieniowania.

Efekt w modelu:

```text
większa odległość od gwiazdy → niższa temperatura
większa jasność gwiazdy      → wyższa temperatura
większe albedo               → niższa temperatura
```

---

# Efekt cieplarniany

## Cel

Efekt cieplarniany podnosi temperaturę powierzchni ponad temperaturę równowagową.

W modelu zależy głównie od składników atmosferycznych i od ogólnego wyniku atmosfery.

## Używany model

```text
greenhouse =
    carbon × 80
  + methane × 120
  + ammonia × 60
  + nitrogen × 20
```

Następnie wynik jest wzmacniany przez atmosferę:

```text
greenhouse_final = greenhouse × (0.3 + atmosphere_score)
```

## Dlaczego tak?

W modelu:

```text
methane  → bardzo silny efekt cieplarniany
carbon   → efekt cieplarniany związany z CO₂ i związkami węgla
ammonia  → dodatkowy gaz cieplarniany i składnik egzotycznych atmosfer
nitrogen → sam nie jest silnym gazem cieplarnianym, ale stabilizuje atmosferę
```

To uproszczenie. Model nie rozróżnia dokładnych związków chemicznych, takich jak CO₂, CH₄, NH₃, N₂, tylko traktuje składniki jako wskaźniki potencjalnej atmosfery.

---

# Temperatura powierzchniowa

## Cel

Temperatura powierzchniowa to finalna temperatura planety po dodaniu efektu cieplarnianego i części ciepła wewnętrznego.

## Używany model

```text
surface_temperature =
    equilibrium_temperature
  + greenhouse_effect
  + internal_heating
```

W kodzie ciepło wewnętrzne przeliczane jest na dodatkowy wkład temperaturowy:

```text
internal_heating_k = internal_heat_score × 20
```

## Dlaczego tak?

Temperatura powierzchni zależy nie tylko od gwiazdy. W przypadku planet lodowych, oceanicznych lub aktywnych geologicznie istotne mogą być też:

- efekt cieplarniany,
- wulkanizm,
- ciepło radiogeniczne,
- ciepło pozostałe po formowaniu planety,
- pływy grawitacyjne.

W tym modelu uwzględnione są głównie:

```text
gwiazda + atmosfera + ciepło wewnętrzne
```

---

# Ciepło wewnętrzne

## Cel

Ciepło wewnętrzne określa, jak aktywne energetycznie jest wnętrze planety.

Wpływa na:

- aktywność wulkaniczną,
- możliwość istnienia podpowierzchniowych oceanów,
- długotrwałą aktywność geologiczną,
- potencjalne źródła energii dla życia.

## Używany model

```text
internal_heat =
    (
      radioactive_elements × 2.0
    + iron_magnesium × 0.5
    + mass_earth × 0.15
    ) / age_billion_years
```

Wynik jest ograniczany do zakresu `0.0 - 1.0`.

## Dlaczego tak?

Założenia:

```text
więcej pierwiastków radioaktywnych → więcej ciepła radiogenicznego
większa masa                       → wolniejsze wychładzanie planety
większy udział metali              → bardziej masywne wnętrze
większy wiek                       → mniej ciepła wewnętrznego
```

Młode planety są zwykle bardziej aktywne geologicznie niż stare planety.

---

# Wulkanizm

## Cel

Wulkanizm opisuje poziom aktywności geologicznej planety.

Wynik jest w zakresie `0.0 - 1.0`.

## Używany model

```text
volcanism =
    radioactive_elements × 0.45
  + sulfur × 0.20
  + titanium × 0.10
  + iron_magnesium × 0.10
  + mass_factor × 0.15
```

Następnie wynik mnożony jest przez czynnik wieku:

```text
age_factor = clamp(1.2 - age_billion_years / 5.0, 0.2, 1.2)
```

## Dlaczego tak?

W modelu:

```text
radioactive_elements → źródło ciepła wewnętrznego
sulfur               → wskaźnik aktywności wulkanicznej i gazów wulkanicznych
titanium             → składnik skorupy i skał magmowych
iron_magnesium       → składniki skał płaszcza i skorupy
mass                 → większa planeta dłużej utrzymuje ciepło
age                  → starsza planeta jest zwykle mniej aktywna
```

Model nie symuluje prawdziwej tektoniki płyt, ale daje logiczny wskaźnik aktywności geologicznej.

---

# Atmosfera

## Cel

Atmosphere score określa, czy planeta ma warunki do utrzymania istotnej atmosfery.

Wynik jest w zakresie `0.0 - 1.0`.

## Używany model

```text
atmosphere =
    nitrogen × 0.25
  + methane × 0.15
  + ammonia × 0.15
  + water_ice × 0.15
  + volcanism_score × 0.20
  + min(gravity, 2.0) × 0.10
```

Potem wynik jest osłabiany przez niekorzystne warunki:

```text
if gravity < 0.4:
    atmosphere *= 0.4

if escape_velocity < 5.0:
    atmosphere *= 0.6

if surface_temperature > 450 K:
    atmosphere *= 0.5

if surface_temperature < 120 K:
    atmosphere *= 0.7
```

## Dlaczego tak?

Atmosfera zależy od kilku rzeczy.

Po pierwsze, planeta musi mieć lotne składniki:

```text
nitrogen
methane
ammonia
water
```

Po drugie, aktywność wulkaniczna może dostarczać gazów do atmosfery.

Po trzecie, planeta musi mieć wystarczającą grawitację i prędkość ucieczki, żeby atmosfera nie uciekła łatwo w przestrzeń kosmiczną.

Po czwarte, ekstremalna temperatura może utrudniać stabilność atmosfery.

Wynik `atmosphere_score` nie oznacza dokładnego ciśnienia atmosferycznego. Jest to indeks jakości atmosfery.

---

# Ciekła woda

## Cel

Model sprawdza, czy warunki pozwalają na istnienie ciekłej wody.

## Używany model

Temperatura określa bazową możliwość istnienia ciekłej wody:

```text
273.15 K - 373.15 K → najlepszy zakres
240 K - 273.15 K    → częściowo możliwa woda, np. pod lodem
373.15 K - 450 K    → możliwa tylko przy wysokim ciśnieniu
poza zakresem       → brak ciekłej wody na powierzchni
```

Potem wynik jest modyfikowany przez atmosferę:

```text
pressure_factor = atmosphere_score / 0.4
liquid_water_factor = temperature_factor × pressure_factor
```

## Dlaczego tak?

Woda ciekła wymaga odpowiedniego zakresu temperatury i ciśnienia.

Atmosfera jest ważna, ponieważ przy zbyt niskim ciśnieniu woda może sublimować lub szybko parować.

---

# Pokrycie oceanami

## Cel

Ocean coverage określa szacowaną część powierzchni pokrytą oceanami.

Wynik jest w zakresie `0.0 - 1.0`.

## Używany model

```text
ocean_coverage = water_ice × liquid_water_factor × 3.0
```

Wynik jest ograniczony do zakresu `0.0 - 1.0`.

## Dlaczego tak?

Sama obecność wody/lodu nie wystarcza. Potrzebne są jeszcze warunki, w których woda może być ciekła.

Dlatego oceaniczność zależy od:

```text
ilości wody/lodu
temperatury
atmosfery
```

Współczynnik `3.0` wzmacnia wpływ wody, ponieważ nawet umiarkowany udział wody w składzie może dać duże pokrycie powierzchni oceanami.

---

# Chemistry score

## Cel

Chemistry score opisuje, czy planeta ma podstawowe składniki chemiczne sprzyjające życiu.

Wynik jest w zakresie `0.0 - 1.0`.

## Używany model

```text
chemistry =
    carbon × 0.25
  + nitrogen × 0.25
  + phosphorus × 0.20
  + water_ice × 0.20
  + sulfur × 0.10
```

Następnie wynik jest wzmacniany:

```text
chemistry_score = chemistry × 3.0
```

i ograniczany do `0.0 - 1.0`.

## Dlaczego tak?

Model bazuje na prostym założeniu, że życie podobne do ziemskiego lub częściowo egzotyczne potrzebuje:

```text
carbon      → chemia organiczna
nitrogen    → aminokwasy, atmosfera, cykle biochemiczne
phosphorus  → DNA/RNA/ATP w biologii ziemskiej
water       → rozpuszczalnik i środowisko reakcji
sulfur      → chemia chemosyntetyczna i źródła energii
```

To nie jest dokładna biochemia. Jest to indeks potencjału chemicznego.

---

# Stability score

## Cel

Stability score określa, czy planeta ma stabilne warunki środowiskowe.

Wynik jest w zakresie `0.0 - 1.0`.

## Używany model

Startowo:

```text
stability = 1.0
```

Następnie nakładane są kary:

```text
if gravity < 0.3 or gravity > 3.0:
    stability *= 0.5

if volcanism_score > 0.85:
    stability *= 0.6

if atmosphere_score < 0.2:
    stability *= 0.4

if surface_temperature < 180 K or surface_temperature > 500 K:
    stability *= 0.2
```

## Dlaczego tak?

Środowisko może być nieprzyjazne mimo obecności wody lub dobrej chemii.

Czynniki destabilizujące:

```text
za niska grawitacja      → utrata atmosfery
za wysoka grawitacja     → trudne warunki dla życia podobnego do ziemskiego
ekstremalny wulkanizm    → niestabilna powierzchnia
bardzo cienka atmosfera  → brak ochrony i ciśnienia
ekstremalna temperatura  → brak stabilnej biosfery powierzchniowej
```

---

# Habitability score

## Cel

Habitability score to główny wynik przeżywalności planety.

Wynik jest w zakresie `0 - 100`.

Nie oznacza on dokładnego prawdopodobieństwa życia. Jest to syntetyczny indeks warunków sprzyjających przetrwaniu życia podobnego do ziemskiego.

## Używany model

```text
habitability =
    temperature_score × 0.30
  + ocean_coverage × 0.25
  + atmosphere_score × 0.20
  + chemistry_score × 0.15
  + stability_score × 0.10
```

Następnie:

```text
habitability_score = habitability × 100
```

## Składniki wyniku

### Temperature score

Temperatura oceniana jest funkcją dzwonową:

```text
temperature_score = 1 - abs(surface_temperature - ideal) / tolerance
```

W modelu:

```text
ideal = 288 K
tolerance = 120 K
```

Czyli najlepsza temperatura jest bliska ziemskiej średniej temperaturze powierzchni.

### Ocean coverage

Woda jest jednym z najważniejszych czynników, dlatego ma wagę `0.25`.

### Atmosphere score

Atmosfera jest potrzebna do ciśnienia, ochrony i stabilności klimatu, dlatego ma wagę `0.20`.

### Chemistry score

Chemia życia ma wagę `0.15`.

### Stability score

Stabilność ma wagę `0.10`, ponieważ nawet chemicznie dobra planeta może być nieprzyjazna, jeśli ma ekstremalne warunki.

## Dlaczego takie wagi?

Wagi dobrano heurystycznie:

```text
temperatura  → najważniejszy pojedynczy czynnik
woda         → bardzo ważna dla życia podobnego do ziemskiego
atmosfera    → ważna dla ochrony i ciśnienia
chemia       → potrzebna do procesów biologicznych
stabilność   → kara za warunki ekstremalne
```

To można później łatwo zmieniać i kalibrować.

---

# Klasyfikacja planety

Po obliczeniu parametrów planeta dostaje opisową klasyfikację.

Przykładowe klasy:

```text
Temperate habitable world
Ocean world
Frozen world
Hot greenhouse world
Volcanic world
Airless rocky world
Marginal terrestrial world
```

## Logika klasyfikacji

```text
habitability_score >= 75
→ Temperate habitable world

ocean_coverage > 0.6
→ Ocean world

surface_temperature_c < -80
→ Frozen world

surface_temperature_c > 120
→ Hot greenhouse world

volcanism_score > 0.75
→ Volcanic world

atmosphere_score < 0.2
→ Airless rocky world

otherwise
→ Marginal terrestrial world
```

Klasyfikacja jest uproszczona i ma służyć głównie do szybkiego zrozumienia wyniku.

---

# Ostrzeżenia środowiskowe

Model generuje ostrzeżenia, jeśli planeta ma skrajne parametry.

Przykłady:

```text
Very low gravity may prevent long-term atmosphere retention.
Very high gravity would be dangerous for Earth-like organisms.
Surface temperature is extremely low.
Surface temperature is extremely high.
Atmosphere is probably too thin for surface habitability.
Extreme volcanism may destabilize the surface environment.
```

Ostrzeżenia pomagają interpretować wynik habitability score.

---

# Interpretacja przykładowego wyniku

Przykład:

```json
{
  "density_g_cm3": 3.161,
  "radius_earth": 1.203,
  "gravity_g": 0.69,
  "surface_temperature_c": -9.386,
  "atmosphere_score": 0.12,
  "ocean_coverage": 0.072,
  "habitability_score": 35.051,
  "classification": "Airless rocky world"
}
```

Interpretacja:

Planeta ma stosunkowo niską gęstość, więc przy masie `1.0 M⊕` jej promień wychodzi większy niż ziemski. Przez większy promień grawitacja powierzchniowa spada do około `0.69 g`.

Temperatura powierzchniowa jest poniżej zera, ale nie ekstremalnie niska. Główny problem to bardzo niski wynik atmosfery `0.12`, przez co planeta zostaje sklasyfikowana jako `Airless rocky world`.

Niskie `ocean_coverage` wynika z tego, że przy słabej atmosferze i temperaturze poniżej zera ciekła woda na powierzchni jest mało prawdopodobna.

Habitability score `35.051` oznacza planetę częściowo interesującą, ale raczej trudną do przetrwania na powierzchni.

---

# Ograniczenia modelu

Model ma kilka istotnych ograniczeń.

## 1. Brak pełnej atmosfery chemicznej

Model nie rozróżnia dokładnie gazów takich jak:

```text
CO₂
O₂
N₂
CH₄
NH₃
H₂O vapor
SO₂
```

Zamiast tego używa ogólnych składników jako wskaźników.

## 2. Brak prawdziwej tektoniki

Wulkanizm jest liczony na podstawie składu, masy i wieku. Model nie symuluje płyt tektonicznych, konwekcji płaszcza ani naprężeń skorupy.

## 3. Brak ewolucji w czasie

Planeta jest liczona jako pojedynczy stan, bez historii geologicznej i klimatycznej.

## 4. Brak dokładnego modelu gwiazdy

Gwiazda opisana jest tylko jasnością względem Słońca. Model nie uwzględnia typu widmowego, aktywności gwiazdowej, rozbłysków ani promieniowania UV.

## 5. Brak dokładnej biologii

Habitability score nie oznacza realnego prawdopodobieństwa życia. Jest to indeks warunków środowiskowych.

---

# Dlaczego ten model jest dobry na start?

Ten model jest dobry jako pierwszy etap projektu, ponieważ:

- skład planety realnie wpływa na wynik,
- masa i gęstość wpływają na promień oraz grawitację,
- atmosfera wpływa na temperaturę i wodę,
- woda wpływa na oceaniczność,
- chemia wpływa na potencjał życia,
- wynik jest łatwy do wizualizacji,
- każdy moduł można później ulepszać osobno.

Najważniejsze jest to, że model tworzy spójny pipeline:

```text
composition
→ density
→ radius
→ gravity
→ escape velocity
→ climate
→ atmosphere
→ hydrosphere
→ habitability
→ classification
```

---

# Plan rozwoju

## Etap 1

Backend obliczeniowy:

```text
[x] modele danych
[x] endpoint symulacji
[x] podstawowe parametry fizyczne
[x] habitability score
```

## Etap 2

Tekstury proceduralne:

```text
[ ] surface texture
[ ] height map
[ ] ocean map
[ ] temperature map
[ ] volcanism map
[ ] habitability map
```

## Etap 3

Frontend:

```text
[ ] React + TypeScript
[ ] suwaki składu
[ ] panel wyników
[ ] wizualizacja 3D planety
```

## Etap 4

Lepsza symulacja:

```text
[ ] typy biosfery
[ ] mapa lokalnej przeżywalności
[ ] atmosfera jako shader
[ ] chmury
[ ] presety planet
[ ] zapisywanie konfiguracji planety
```

---

# Uruchomienie

## Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instalacja zależności:

```bash
pip install -r requirements.txt
```

Start API:

```bash
uvicorn app.main:app --reload
```

API będzie dostępne pod adresem:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

# Ważna uwaga

Wyniki generowane przez Planet Genesis są szacunkowe.

Projekt ma charakter edukacyjny, proceduralny i wizualizacyjny. Nie powinien być traktowany jako profesjonalne narzędzie do astrofizyki, klimatologii planetarnej ani astrobiologii.

Docelowo model można rozwijać przez dodawanie bardziej zaawansowanych wzorów, danych empirycznych i oddzielnych modeli dla różnych typów planet.
