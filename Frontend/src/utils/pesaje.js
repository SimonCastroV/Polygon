export const VERIFICACIONES_PESAJE = [
  ['productos_retirados', 'Se retiraron todos los productos del lote anterior'],
  [
    'sin_restos_lote_anterior',
    'No quedan pigmentos, etiquetas o documentos en el proceso del lote anterior',
  ],
  ['balanzas_limpias', 'Balanzas niveladas, limpias y sin residuos'],
  ['superficies_limpias', 'Superficies y mesas limpias'],
  ['utensilios_limpios', 'Utensilios limpios y en buen estado'],
  ['piso_limpio', 'Piso limpio y sin derrames'],
  ['area_ordenada', 'Área ordenada y acondicionada para nuevo lote'],
  ['bolsa_identificada', 'Bolsa provisional de empaque correctamente identificada'],
  ['epp_adecuado', 'Uso adecuado de EPP'],
  ['residuos_dispuestos', 'Residuos del lote anterior dispuestos correctamente'],
]

export const VERIFICACIONES_CRITICAS = [
  [
    'critico_area_equipos_limpios',
    'El área (pisos, paredes) y los equipos a operar se encuentran limpios y libres de residuos.',
  ],
  ['critico_limpieza_anterior_liberada', 'Se libera la limpieza ejecutada del producto anterior.'],
  [
    'critico_uniforme_epp',
    'El personal que participa en la operación porta uniforme limpio, completo y utiliza los EPP.',
  ],
  [
    'critico_mp_identificadas',
    'Las MP presentes en el área están identificadas, segregadas y corresponden con la OP a fabricar.',
  ],
  [
    'critico_equipos_aptos',
    'Los equipos y periféricos requeridos para la fabricación se encuentran disponibles y aptos para iniciar la operación.',
  ],
  [
    'critico_sin_actividades_simultaneas',
    'No se realizan actividades simultáneas (limpieza, mantenimiento u otras) que puedan generar contaminación del producto.',
  ],
  [
    'critico_ambiente_adecuado',
    'Las condiciones ambientales del área son adecuadas para iniciar pesaje.',
  ],
  ['critico_cero_pellets', 'Se cumple con “Cero Pellets en el Piso”.'],
  [
    'critico_sin_condiciones_inseguras',
    'No se identifican condiciones inseguras o desviaciones que afecten la integridad del producto.',
  ],
  [
    'critico_liberacion_autorizada',
    '¿Se autoriza la liberación de las condiciones operacionales para iniciar el pesaje del lote?',
  ],
]
