# Portal de Investigación UNPHU

Landing institucional que conecta los distintos portales de investigación de la UNPHU. La página se regenera a partir de un Excel maestro.

## Estructura

```text
portal-investigacion-unphu/
├── index.html
├── css/
│   └── styles.css
├── js/
│   ├── app.js
│   └── portales.generated.js      # generado automáticamente
├── assets/
│   └── icons/
│       ├── financiacion.png
│       ├── agenda.png
│       └── laboratorio.png
├── datos/
│   └── portal_investigacion_unphu.xlsx
├── scripts/
│   └── generar_portal.py
└── .github/workflows/
    └── publicar.yml
```

## Excel maestro

La hoja utilizada debe llamarse `PORTALES` y contener estas columnas:

| Campo | Función |
|---|---|
| ID | Identificador único |
| Nombre | Nombre visible de la tarjeta |
| Descripcion | Texto descriptivo |
| URL | Enlace del portal |
| Icono | Nombre del archivo dentro de `assets/icons/` |
| Categoria | Etiqueta visible |
| Orden | Orden de presentación |
| Estado | `Activo` para mostrar; cualquier otro valor se oculta |
| Destacado | `Sí` aplica el tratamiento visual destacado |

## Cómo actualizar el portal

1. Edita `datos/portal_investigacion_unphu.xlsx`.
2. Si agregas una tarjeta nueva, coloca también su icono PNG en `assets/icons/` y escribe exactamente ese nombre en la columna `Icono`.
3. Sube/commitea los cambios a la rama `main`.
4. GitHub Actions ejecutará `scripts/generar_portal.py`.
5. El generador valida el Excel, crea `js/portales.generated.js` y GitHub Pages publica el sitio.

No es necesario editar `index.html` para añadir, quitar o reordenar tarjetas.

## Primera publicación en GitHub Pages

1. Crea el repositorio `portal-investigacion-unphu`.
2. Sube todo el contenido de esta carpeta a la rama `main`.
3. En GitHub abre **Settings → Pages**.
4. En **Build and deployment → Source**, selecciona **GitHub Actions**.
5. Abre la pestaña **Actions** y comprueba que el workflow **Regenerar y publicar Portal de Investigación** termine correctamente.

La URL resultante será, si mantienes ese nombre de repositorio:

`https://wilintec.github.io/portal-investigacion-unphu/`

## Regeneración local

No requiere instalar paquetes Python adicionales:

```bash
python scripts/generar_portal.py
```

Después puedes abrir `index.html` directamente en el navegador.
