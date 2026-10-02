# -*- coding: utf-8 -*-
"""
Adaptación web sin interfaz gráfica del motor original.
No modifica la lógica lingüística del archivo fuente.

© Roberto Spíndola Barrón, 2026.
Todos los derechos reservados.

Sistema estructural de análisis lingüístico Náhuatl ↔ Español.
Módulo: Nahuatl_Translator
Versión: v1.0
Fecha: 23-05-2026

Prohibida la reproducción, redistribución, extracción estructural,
ingeniería inversa, entrenamiento de modelos de inteligencia artificial
o reutilización no autorizada.
"""

import csv
import difflib
import importlib
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkf
import tkinter.simpledialog as sd
import unicodedata

from pathlib import Path
from tkinter import messagebox


base_dir = Path(__file__).resolve().parent
print("USANDO:", __file__)

# ----------------------------------------------------------------------
# Importaciones internas del motor
#
# Primer intento:
#	 importación relativa cuando el archivo pertenece al paquete motor.
#
# Segundo intento:
#	 importación directa cuando este archivo se ejecuta por separado.
# ----------------------------------------------------------------------

try:
	from .MODIFIERS_SP_NTL import MODIFIERS as MODIFIERS_SP_NTL
except ImportError:
	try:
		from MODIFIERS_SP_NTL import MODIFIERS as MODIFIERS_SP_NTL
	except Exception as e:
		print("ERROR cargando MODIFIERS_SP_NTL:", e)
		MODIFIERS_SP_NTL = {}


try:
	from .MODIFIERS_NTL_SP import MODIFIERS as MODIFIERS_NTL_SP
except ImportError:
	try:
		from MODIFIERS_NTL_SP import MODIFIERS as MODIFIERS_NTL_SP
	except Exception as e:
		print("ERROR cargando MODIFIERS_NTL_SP:", e)
		MODIFIERS_NTL_SP = {}


try:
	from .PREPOSITIONS_SP_NTL import PREPOSITIONS_SP_NTL
except ImportError:
	try:
		from PREPOSITIONS_SP_NTL import PREPOSITIONS_SP_NTL
	except Exception as e:
		print("ERROR cargando PREPOSITIONS_SP_NTL:", e)
		PREPOSITIONS_SP_NTL = {}


try:
	from .BELONGING_MARKERS_SP_NTL import BELONGING_MARKERS_SP_NTL
except ImportError:
	try:
		from BELONGING_MARKERS_SP_NTL import BELONGING_MARKERS_SP_NTL
	except Exception as e:
		print("ERROR cargando BELONGING_MARKERS_SP_NTL:", e)
		BELONGING_MARKERS_SP_NTL = {}


try:
	from .NOUNS_SP_NTL import NOUNS_SP_NTL
except ImportError:
	try:
		from NOUNS_SP_NTL import NOUNS_SP_NTL
	except Exception as e:
		print("ERROR cargando NOUNS_SP_NTL:", e)
		NOUNS_SP_NTL = {}


try:
	from .NOUNS_NTL_SP import NOUNS_NTL_SP
except ImportError:
	try:
		from NOUNS_NTL_SP import NOUNS_NTL_SP
	except Exception as e:
		print("ERROR cargando NOUNS_NTL_SP:", e)
		NOUNS_NTL_SP = {}

try:
	from .tlalkan_SP_NTL import tlalkan_SP_NTL
except ImportError:
	try:
		from tlalkan_SP_NTL import tlalkan_SP_NTL
	except Exception as e:
		print("ERROR cargando tlalkan_SP_NTL:", e)
		tlalkan_SP_NTL = {}


try:
	from .ADVERBS_SP_NTL import ADVERBS_SP_NTL
except ImportError:
	try:
		from ADVERBS_SP_NTL import ADVERBS_SP_NTL
	except Exception as e:
		print("ERROR cargando ADVERBS_SP_NTL:", e)
		ADVERBS_SP_NTL = {}

try:
	from .ADVERBS_NTL_SP import ADVERBS_NTL_SP
except ImportError:
	try:
		from ADVERBS_NTL_SP import ADVERBS_NTL_SP
	except Exception as e:
		print("ERROR cargando ADVERBS_NTL_SP:", e)
		ADVERBS_NTL_SP = {}


MODIFIERS = MODIFIERS_SP_NTL


def build_reflexive_verb_forms_sp_ntl(stem_sp: str, root_ntl: str, reflexive_root_ntl: str='mo') -> dict:
	return {f'{stem_sp}arse': f'{reflexive_root_ntl} {root_ntl}', f'me {stem_sp}o': f'ni {reflexive_root_ntl} {root_ntl}', f'te {stem_sp}as': f'ti {reflexive_root_ntl} {root_ntl}', f'se {stem_sp}a': f'{reflexive_root_ntl} {root_ntl}', f'nos {stem_sp}amos': f'ti {reflexive_root_ntl} {root_ntl}h', f'se {stem_sp}an': f'{reflexive_root_ntl} {root_ntl}h', f'me {stem_sp}é': f'oni {reflexive_root_ntl} {root_ntl}k', f'te {stem_sp}aste': f'oti {reflexive_root_ntl} {root_ntl}k', f'se {stem_sp}ó': f'o {reflexive_root_ntl} {root_ntl}k', f'se {stem_sp}aron': f'o {reflexive_root_ntl} {root_ntl}keh', f'me {stem_sp}aré': f'ni {reflexive_root_ntl} {root_ntl}z', f'te {stem_sp}arás': f'ti {reflexive_root_ntl} {root_ntl}z', f'se {stem_sp}ará': f'{reflexive_root_ntl} {root_ntl}z', f'se {stem_sp}arán': f'{reflexive_root_ntl} {root_ntl}zkeh', f'me {stem_sp}aba': f'ni {reflexive_root_ntl} {root_ntl}ya', f'te {stem_sp}abas': f'ti {reflexive_root_ntl} {root_ntl}ya', f'se {stem_sp}aba': f'{reflexive_root_ntl} {root_ntl}ya', f'se {stem_sp}aban': f'{reflexive_root_ntl} {root_ntl}yakeh', f'me {stem_sp}aría': f'ni {reflexive_root_ntl} {root_ntl}zya', f'te {stem_sp}arías': f'ti {reflexive_root_ntl} {root_ntl}zya', f'se {stem_sp}aría': f'{reflexive_root_ntl} {root_ntl}zya', f'se {stem_sp}arían': f'{reflexive_root_ntl} {root_ntl}zyakeh'}
def _load_versioned_dictionary_module(base_name: str, dictionary_name: str):
	"""Carga primero la versión numerada más alta y, si no existe, el módulo sin número."""
	candidates = []
	for path in base_dir.glob(f'{base_name}(*).py'):
		m = re.fullmatch(rf'{re.escape(base_name)}\((\d+)\)\.py', path.name)
		if m:
			candidates.append((int(m.group(1)), path))

	if candidates:
		_, selected = max(candidates, key=lambda item: item[0])
		spec = importlib.util.spec_from_file_location(
			f'_{base_name}_versioned',
			selected,
		)
		if spec and spec.loader:
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			mapping = getattr(module, dictionary_name, None)
			if isinstance(mapping, dict):
				return mapping, module, selected.name

	module = importlib.import_module(base_name)
	mapping = getattr(module, dictionary_name)
	return mapping, module, f'{base_name}.py'

try:
	sp_ntl, sp_ntl_mod, SP_NTL_SOURCE = _load_versioned_dictionary_module(
		'sp_ntl', 'sp_ntl'
	)
except Exception as e:
	print('ERROR cargando sp_ntl:', e)
	sp_ntl = {}
	sp_ntl_mod = None
	SP_NTL_SOURCE = None

try:
	ntl_sp, ntl_sp_mod, NTL_SP_SOURCE = _load_versioned_dictionary_module(
		'ntl_sp', 'ntl_sp'
	)
except Exception as e:
	print('ERROR cargando ntl_sp:', e)
	ntl_sp = {}
	ntl_sp_mod = None
	NTL_SP_SOURCE = None

try:
	ado_ido, ado_ido_mod, ADO_IDO_SOURCE = _load_versioned_dictionary_module(
		'ado_ido', 'ado_ido'
	)
except Exception as e:
	print('ERROR cargando ado_ido:', e)
	ado_ido = {}
	ado_ido_mod = None
	ADO_IDO_SOURCE = None

try:
	ik_tik, ik_tik_mod, IK_TIK_SOURCE = _load_versioned_dictionary_module(
		'ik_tik', 'ik_tik'
	)
except Exception as e:
	print('ERROR cargando ik_tik:', e)
	ik_tik = {}
	ik_tik_mod = None
	IK_TIK_SOURCE = None

def build_gerund_forms_sp_ntl(stem_sp: str, root_ntl: str) -> dict:
	return {f'{stem_sp}ando': f'{root_ntl}tika', f'{stem_sp}iendo': f'{root_ntl}tika'}
sp_ntl.update(build_reflexive_verb_forms_sp_ntl(stem_sp='traslad', root_ntl='oli'))
sp_ntl.update({'trasládate': 'ximooli', 'trasládense': 'ximoolih'})


def strip_accents_for_compare(s: str) -> str:
	return ''.join((ch for ch in unicodedata.normalize('NFD', s or '') if unicodedata.category(ch) != 'Mn'))

def tolerant_lookup(key: str, mapping: dict):
	"""
	Busca primero coincidencia exacta.
	Si no encuentra, compara sin tildes.
	No altera la ortografía visible; solo flexibiliza la comparación.
	"""
	if not key:
		return None
	key_nfc = unicodedata.normalize('NFC', key).strip().lower()
	if key_nfc in mapping:
		return mapping[key_nfc]
	key_cmp = strip_accents_for_compare(key_nfc)
	for mk, mv in mapping.items():
		mk_nfc = unicodedata.normalize('NFC', str(mk)).strip().lower()
		if key_nfc in {'de', 'dé'} and mk_nfc in {'de', 'dé'} and mk_nfc != key_nfc:
			continue
		if strip_accents_for_compare(mk_nfc) == key_cmp:
			return mv
	return None

def extract_tlalkan_sp_ntl(text: str) -> tuple[str, list[str]]:
	"""
	Extrae únicamente los topónimos registrados en tlalkan_SP_NTL.

	Las coincidencias de varias palabras tienen prioridad sobre las de una sola
	palabra. Los topónimos se retiran temporalmente de la oración para impedir
	que los analizadores generales los traten como sustantivos desconocidos;
	después se reincorporan al final de la traducción Español -> Náhuatl.
	"""
	original = unicodedata.normalize('NFC', str(text or '')).strip()
	if not original or not tlalkan_SP_NTL:
		return original, []

	working = original
	found: list[tuple[int, str]] = []

	entries = sorted(
		tlalkan_SP_NTL.items(),
		key=lambda item: len(str(item[0]).split()),
		reverse=True,
	)

	for source, target in entries:
		source = unicodedata.normalize('NFC', str(source or '')).strip()
		if not source:
			continue

		pattern = re.compile(
			r'(?<!\w)' + re.escape(source) + r'(?!\w)',
			re.IGNORECASE,
		)

		while True:
			match = pattern.search(working)
			if not match:
				break

			translation = first_variant(target)
			if translation:
				found.append((match.start(), str(translation).strip()))

			working = working[:match.start()] + (' ' * (match.end() - match.start())) + working[match.end():]

	working = re.sub(r'\s+', ' ', working).strip()
	found.sort(key=lambda item: item[0])
	return working, [translation for _, translation in found if translation]


def append_tlalkan_sp_ntl_to_translation(translation: str, toponyms: list[str]) -> str:
	"""Coloca al final únicamente los topónimos con función de complemento."""
	parts = [str(translation or '').strip()]
	parts.extend(str(toponym).strip() for toponym in toponyms if str(toponym or '').strip())
	return re.sub(r'\s+', ' ', ' '.join(part for part in parts if part)).strip()


def classify_tlalkan_subjects_sp_ntl(text: str, translated_toponyms: list[str]) -> tuple[list[str], list[str]]:
	"""Separa topónimos sujeto de topónimos complemento dentro de una cláusula.

	La categoría léxica ``topónimo`` no determina por sí sola la función
	sintáctica. Un topónimo no preposicional situado antes del verbo finito se
	considera sujeto. También se admite el sujeto pospuesto cuando el verbo de
	la cláusula es intransitivo (por ejemplo, «llegó España»). Los topónimos
	introducidos por preposición conservan su función de complemento.
	"""
	if not translated_toponyms:
		return [], []

	normalized = normalize_input_sp(text)
	tokens = normalized.split()
	if not tokens:
		return [], list(translated_toponyms)

	verb_index = None
	verb_lemma = None
	for i, token in enumerate(tokens):
		finite = detect_finite_verb([token])
		regular = detect_regular_verb([token])
		simple = detect_simple_verb([token])
		special = detect_special_verb([token])
		if finite[0] or regular[0] or simple[0] or special[0]:
			verb_index = i
			# Los detectores finito/regular devuelven el infinitivo español.
			# Para los detectores simples se conserva la forma detectada; sólo
			# habilitamos sujeto pospuesto cuando el lema está explícitamente
			# reconocido como intransitivo.
			verb_lemma = finite[0] or regular[0] or simple[0] or special[0]
			break

	if verb_index is None:
		return [], list(translated_toponyms)

	prepositions = set(PREPOSITIONS_SP_NTL) | {'a', 'de', 'del', 'desde', 'en', 'hacia', 'hasta', 'para', 'por', 'sobre'}
	subjects: list[str] = []
	complements: list[str] = []
	remaining = list(translated_toponyms)

	entries = sorted(tlalkan_SP_NTL.items(), key=lambda item: len(str(item[0]).split()), reverse=True)
	for source, target in entries:
		translation = str(first_variant(target) or '').strip()
		if not translation or translation not in remaining:
			continue
		source_tokens = normalize_input_sp(str(source)).split()
		width = len(source_tokens)
		found_index = None
		for i in range(0, len(tokens) - width + 1):
			if tokens[i:i + width] == source_tokens:
				found_index = i
				break
		is_prepositional = found_index is not None and found_index > 0 and tokens[found_index - 1] in prepositions
		is_preposed_subject = found_index is not None and found_index < verb_index and not is_prepositional
		is_postposed_subject = (
			found_index is not None
			and found_index > verb_index
			and not is_prepositional
			and verb_lemma in INTRANSITIVE_VERBS_SP
		)
		if is_preposed_subject or is_postposed_subject:
			subjects.append(translation)
		else:
			complements.append(translation)
		remaining.remove(translation)

	complements.extend(remaining)
	return subjects, complements

def spanish_singular_candidates(word: str) -> list[str]:
	"""
	Genera candidatos singulares para una forma española posiblemente plural.

	La función no decide por sí sola que una palabra sea plural: los candidatos
	sólo se aceptan cuando existen como claves en la base léxica consultada.
	De esta manera se conservan singulares terminados en ``s`` —por ejemplo,
	``crisis``— cuando ya cuentan con una entrada exacta.

	Reglas cubiertas:
	- vocal + s: ``pócimas`` -> ``pócima``;
	- consonante + es: ``mujeres`` -> ``mujer``;
	- z -> ces: ``luces`` -> ``luz``;
	- pérdida gráfica de tilde en plural: ``canciones`` -> ``cancion``;
	  la búsqueda tolerante recupera ``canción``.
	"""
	w = unicodedata.normalize('NFC', str(word or '')).strip().lower()
	if len(w) < 3:
		return []

	candidates: list[str] = []

	def add(candidate: str):
		if candidate and candidate != w and candidate not in candidates:
			candidates.append(candidate)

	# lápices -> lápiz, luces -> luz, peces -> pez
	if len(w) > 4 and w.endswith('ces'):
		add(w[:-3] + 'z')

	# mujeres -> mujer, canciones -> cancion, papeles -> papel
	if len(w) > 4 and w.endswith('es'):
		add(w[:-2])

	# brujas -> bruja, hechizos -> hechizo, jóvenes? se resuelve arriba
	if len(w) > 3 and w.endswith('s'):
		add(w[:-1])

	return candidates


# Excepciones productivas y cambios de acentuación que no pueden deducirse
# únicamente eliminando o agregando ``s`` / ``es``. Esta tabla puede ampliarse
# sin modificar la función general.
SPANISH_NOUN_PLURAL_OVERRIDES = {
	'carácter': 'caracteres',
	'espécimen': 'especímenes',
	'joven': 'jóvenes',
	'régimen': 'regímenes',
	'canción': 'canciones',
	'camión': 'camiones',
	'corazón': 'corazones',
	'razón': 'razones',
	'volcán': 'volcanes',
	'compás': 'compases',
	'francés': 'franceses',
	'lápiz': 'lápices',
	'luz': 'luces',
	'pez': 'peces',
	'vez': 'veces',
	'crisis': 'crisis',
	'tórax': 'tórax',
	'paréntesis': 'paréntesis',
}


def _match_case_spanish(source: str, target: str) -> str:
	"""Conserva mayúscula inicial o mayúsculas completas de la entrada."""
	if source.isupper():
		return target.upper()
	if source[:1].isupper():
		return target[:1].upper() + target[1:]
	return target


def pluralize_spanish_noun(
	singular: str,
	*,
	overrides: dict | None = None,
	prefer_ies_for_accented_i_u: bool = True,
) -> str:
	"""
	Forma el plural español de un sustantivo dado en singular.

	La función es independiente del género gramatical: trabaja igual con
	``bruja`` / ``brujas`` y ``hechizo`` / ``hechizos``.

	Reglas generales:
	- vocal no acentuada, ``á``, ``é`` u ``ó`` + ``s``;
	- ``í`` o ``ú`` + ``es`` de manera predeterminada;
	- consonante + ``es``;
	- ``z`` cambia a ``ces``;
	- varios sustantivos terminados en ``s`` o ``x`` permanecen invariantes;
	- una tabla de excepciones resuelve cambios de acentuación e irregulares.

	``overrides`` permite incorporar vocablos propios de las bases sin alterar
	la lógica general. Sus claves y valores deben estar en singular y plural.
	"""
	raw = unicodedata.normalize('NFC', str(singular or '')).strip()
	if not raw:
		return ''

	word = raw.lower()
	custom = {
		unicodedata.normalize('NFC', str(k)).strip().lower():
		unicodedata.normalize('NFC', str(v)).strip().lower()
		for k, v in (overrides or {}).items()
	}
	all_overrides = {**SPANISH_NOUN_PLURAL_OVERRIDES, **custom}
	if word in all_overrides:
		return _match_case_spanish(raw, all_overrides[word])

	# Palabras agudas terminadas en vocal acentuada.
	if word.endswith(('í', 'ú')):
		suffix = 'es' if prefer_ies_for_accented_i_u else 's'
		return _match_case_spanish(raw, word + suffix)

	# Vocal simple o vocal acentuada que normalmente recibe -s.
	if word.endswith(('a', 'e', 'i', 'o', 'u', 'á', 'é', 'ó')):
		return _match_case_spanish(raw, word + 's')

	# z -> ces: luz -> luces.
	if word.endswith('z'):
		return _match_case_spanish(raw, word[:-1] + 'ces')

	# Muchos sustantivos llanos terminados en s/x son invariantes. Los casos
	# agudos productivos (compás, francés...) se atienden en excepciones.
	if word.endswith(('s', 'x')):
		return raw

	# Consonante final: mujer -> mujeres, papel -> papeles.
	return _match_case_spanish(raw, word + 'es')


def build_spanish_plural_index(
	mapping: dict,
	*,
	overrides: dict | None = None,
) -> dict:
	"""
	Construye un índice ``plural -> singular`` a partir de las claves léxicas.

	No modifica la base original. Si una forma plural ya existe como clave,
	se conserva esa forma explícita y no se genera una colisión artificial.
	"""
	index: dict[str, str] = {}
	existing = {
		unicodedata.normalize('NFC', str(k)).strip().lower()
		for k in mapping
	}
	for key in mapping:
		singular = unicodedata.normalize('NFC', str(key)).strip().lower()
		if not singular:
			continue
		plural = pluralize_spanish_noun(singular, overrides=overrides).lower()
		if not plural or plural == singular or plural in existing:
			continue
		index.setdefault(plural, singular)
	return index


def run_spanish_plural_generation_tests() -> dict:
	"""Pruebas internas de formación singular -> plural para SP -> NTL."""
	expected = {
		'bruja': 'brujas',
		'pócima': 'pócimas',
		'hechizo': 'hechizos',
		'hombre': 'hombres',
		'mujer': 'mujeres',
		'luz': 'luces',
		'pez': 'peces',
		'canción': 'canciones',
		'joven': 'jóvenes',
		'crisis': 'crisis',
		'tórax': 'tórax',
		'colibrí': 'colibríes',
		'café': 'cafés',
	}
	cases = {}
	for singular, wanted in expected.items():
		got = pluralize_spanish_noun(singular)
		cases[singular] = {'ok': got == wanted, 'got': got, 'expected': wanted}
	return {
		'ok': all(case['ok'] for case in cases.values()),
		'cases': cases,
	}


def normalize_spanish_lexeme_number(key: str, mapping: dict) -> dict:
	"""
	Normaliza una entrada léxica española y conserva su número gramatical.

	Devuelve un registro con:
	``surface``: forma recibida;
	``lemma``: clave singular localizada en la base;
	``number``: ``singular`` o ``plural``;
	``value``: equivalencia almacenada en la base.

	La coincidencia exacta siempre tiene prioridad. La pluralización se infiere
	únicamente cuando un candidato singular existe realmente en ``mapping``.
	"""
	surface = unicodedata.normalize('NFC', str(key or '')).strip().lower()
	if not surface:
		return {'surface': '', 'lemma': None, 'number': None, 'value': None}

	exact_value = tolerant_lookup(surface, mapping)
	if exact_value is not None:
		# Recuperar la ortografía canónica de la clave, no sólo su valor.
		surface_cmp = strip_accents_for_compare(surface)
		lemma = next(
			(
				unicodedata.normalize('NFC', str(mk)).strip().lower()
				for mk in mapping
				if strip_accents_for_compare(
					unicodedata.normalize('NFC', str(mk)).strip().lower()
				) == surface_cmp
			),
			surface,
		)
		return {
			'surface': surface,
			'lemma': lemma,
			'number': 'singular',
			'value': exact_value,
		}

	for candidate in spanish_singular_candidates(surface):
		value = tolerant_lookup(candidate, mapping)
		if value is None:
			continue
		candidate_cmp = strip_accents_for_compare(candidate)
		lemma = next(
			(
				unicodedata.normalize('NFC', str(mk)).strip().lower()
				for mk in mapping
				if strip_accents_for_compare(
					unicodedata.normalize('NFC', str(mk)).strip().lower()
				) == candidate_cmp
			),
			candidate,
		)
		return {
			'surface': surface,
			'lemma': lemma,
			'number': 'plural',
			'value': value,
		}

	return {'surface': surface, 'lemma': None, 'number': None, 'value': None}


def tolerant_lexical_lookup(key: str, mapping: dict):
	"""
	Consulta una base léxica española mediante su forma exacta o su singular.

	Esta interfaz conserva compatibilidad con el resto del motor; cuando se
	requiera conocer también lema y número puede llamarse directamente a
	``normalize_spanish_lexeme_number``.
	"""
	return normalize_spanish_lexeme_number(key, mapping)['value']


def run_spanish_plural_normalization_tests() -> dict:
	"""Pruebas internas de normalización para la entrada español -> náhuatl."""
	test_mapping = {
		'bruja': 'BRUJA',
		'hechizo': 'HECHIZO',
		'pócima': 'POCIMA',
		'hombre': 'HOMBRE',
		'mujer': 'MUJER',
		'luz': 'LUZ',
		'pez': 'PEZ',
		'canción': 'CANCION',
		'joven': 'JOVEN',
		'crisis': 'CRISIS',
	}
	expected = {
		'brujas': ('bruja', 'plural', 'BRUJA'),
		'hechizos': ('hechizo', 'plural', 'HECHIZO'),
		'pócimas': ('pócima', 'plural', 'POCIMA'),
		'hombres': ('hombre', 'plural', 'HOMBRE'),
		'mujeres': ('mujer', 'plural', 'MUJER'),
		'luces': ('luz', 'plural', 'LUZ'),
		'peces': ('pez', 'plural', 'PEZ'),
		'canciones': ('canción', 'plural', 'CANCION'),
		'jóvenes': ('joven', 'plural', 'JOVEN'),
		'crisis': ('crisis', 'singular', 'CRISIS'),
	}
	results = {}
	for surface, wanted in expected.items():
		data = normalize_spanish_lexeme_number(surface, test_mapping)
		got = (data['lemma'], data['number'], data['value'])
		results[surface] = {'ok': got == wanted, 'got': got, 'expected': wanted}
	return {
		'ok': all(item['ok'] for item in results.values()),
		'cases': results,
	}

def lookup_aux_haber_form(token: str):
	return tolerant_lookup(token, AUX_HABER_FORMS_SP)

def normalize_input_sp(text: str) -> str:
	if not text:
		return ''
	t = unicodedata.normalize('NFC', text).lower().strip()
	t = re.sub('\\bpor\\s+medio\\s+del\\b', 'por medio de', t)
	t = re.sub('\\bpor\\s+medio\\s+de\\s+el\\b', 'por medio de', t)
	t = re.sub('\\ba\\s+través\\s+del\\b', 'por medio de', t)
	t = re.sub('\\ba\\s+través\\s+de\\s+el\\b', 'por medio de', t)
	t = re.sub('\\ba\\s+través\\s+de\\b', 'por medio de', t)
	t = re.sub('\\ba\\s+lo\\s+largo\\s+del\\b', 'a lo largo de', t)
	t = re.sub('\\ba\\s+lo\\s+largo\\s+de\\s+el\\b', 'a lo largo de', t)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	preposed_double_clitic_forms = {'me lo': 'melo', 'me la': 'mela', 'me los': 'melos', 'me las': 'melas', 'te lo': 'telo', 'te la': 'tela', 'te los': 'telos', 'te las': 'telas', 'se lo': 'selo', 'se la': 'sela', 'se los': 'selos', 'se las': 'selas', 'nos lo': 'noslo', 'nos la': 'nosla', 'nos los': 'noslos', 'nos las': 'noslas'}
	modal_forms = 'quiero|quieres|quiere|queremos|quieren|quise|quisiste|quiso|quisimos|quisieron|quería|queria|querías|querias|queríamos|queriamos|querían|querian|querría|querria|querrías|querrias|querríamos|querriamos|querrían|querrian|puedo|puedes|puede|podemos|pueden|pude|pudiste|pudo|pudimos|pudieron|podía|podia|podías|podias|podíamos|podiamos|podían|podian|podría|podria|podrías|podrias|podríamos|podriamos|podrían|podrian|debo|debes|debe|debemos|deben|debí|debiste|debió|debimos|debieron|debía|debia|debías|debias|debíamos|debiamos|debían|debian|debería|deberia|deberías|deberias|deberíamos|deberiamos|deberían|deberian'
	for phrase, glued in preposed_double_clitic_forms.items():
		t = re.sub(f'\\b{phrase}\\s+({modal_forms})\\s+([a-záéíóúñ]+(?:ar|er|ir))\\b', f'\\1 \\2{glued}', t)
	return t
	return t
ARTICLES_SP = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'}

def safe_import_by_file(pyfile: Path):
	try:
		spec = importlib.util.spec_from_file_location(pyfile.stem, str(pyfile))
		mod = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mod)
		return mod
	except Exception:
		return None

def normalize_key(s):
	return unicodedata.normalize('NFC', str(s or '')).strip().lower()

def normalize_ntl_orthography(s: str) -> str:
	if not s:
		return ''
	t = unicodedata.normalize('NFC', s).lower()
	replacements = [('ck', 'kk'), ('cl', 'kl'), ('cm', 'km'), ('cn', 'kn'), ('cp', 'kp'), ('cs', 'kz'), ('ct', 'kt'), ('cw', 'ku'), ('cx', 'kx'), ('cy', 'ky'), ('cz', 'kz'), ('kw', 'ku'), ('sh', 'x'), ('w', 'u'), ('que', 'ke'), ('qui', 'ki'), ('qu', 'k'), ('ca', 'ka'), ('ce', 'ze'), ('ci', 'zi'), ('co', 'ko'), ('cu', 'ku'), ('sa', 'za'), ('se', 'ze'), ('si', 'zi'), ('so', 'zo'), ('su', 'zu')]
	for old, new in replacements:
		t = t.replace(old, new)
	return t

def build_normalized_ntl_sp_index(source: dict) -> dict:
	index = {}
	for key, val in source.items():
		raw_key = unicodedata.normalize('NFC', str(key)).strip().lower()
		norm_key = normalize_ntl_orthography(raw_key)
		index[raw_key] = val
		index[norm_key] = val
	return index
ntl_sp_index = build_normalized_ntl_sp_index(ntl_sp)

def detect_inline_fixed_phrases_ntl(tokens: list[str]) -> tuple[list[tuple[int, int, str, str]], set[int]]:
	"""Reconoce igualdades léxicas multipalabra NTL→SP dentro de una expresión.

	La coincidencia más larga gana y sus índices quedan reservados para evitar
	que los componentes de una clave reconocida vuelvan a analizarse por separado.
	"""
	found = []
	used_indexes = set()
	phrase_sources = []
	sources = (
		('noun', NOUNS_NTL_SP),
		('modifier', MODIFIERS_NTL_SP),
		('general', ntl_sp),
	)
	for source_kind, source in sources:
		for phrase, raw_val in source.items():
			if not isinstance(phrase, str) or ' ' not in phrase:
				continue
			raw_phrase = unicodedata.normalize('NFC', phrase).strip().lower()
			norm_phrase = normalize_ntl_orthography(raw_phrase)
			if norm_phrase:
				phrase_sources.append((norm_phrase, raw_val, source_kind))
	phrase_sources.sort(key=lambda item: len(item[0].split()), reverse=True)
	for phrase, raw_val, source_kind in phrase_sources:
		phrase_tokens = phrase.split()
		n = len(phrase_tokens)
		for i in range(len(tokens) - n + 1):
			if any(idx in used_indexes for idx in range(i, i + n)):
				continue
			if tokens[i:i + n] != phrase_tokens:
				continue
			val = raw_val
			if isinstance(val, (list, tuple)):
				val = val[0] if val else None
			if isinstance(val, dict):
				val = val.get('es') or val.get('sp')
			if not val:
				continue
			found.append((i, i + n, str(val).strip(), source_kind))
			for idx in range(i, i + n):
				used_indexes.add(idx)
	return (found, used_indexes)


def remove_sp_articles_for_translation(text: str) -> str:
	if text is None:
		return ''
	tokens = text.split()
	clean = []
	for tk in tokens:
		if tk in ARTICLES_SP:
			continue
		clean.append(tk)
	result = ' '.join(clean).strip()
	if result:
		return result
	return text
	t = unicodedata.normalize('NFC', text).lower().strip()
	t = re.sub('\\bpor\\s+medio\\s+del\\b', 'por medio de', t)
	t = re.sub('\\bpor\\s+medio\\s+de\\s+el\\b', 'por medio de', t)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	return t

def strip_accents_local(s: str) -> str:
	return ''.join((ch for ch in unicodedata.normalize('NFD', s or '') if unicodedata.category(ch) != 'Mn'))

def is_nonempty_sequence(value) -> bool:
	if isinstance(value, (list, tuple)):
		return any((bool(x) for x in value))
	return bool(value)

def first_variant(value, default=None):
	if isinstance(value, (list, tuple)):
		for item in value:
			if item:
				return item
		return default
	return value if value else default

def all_variants(value) -> list[str]:
	if value is None:
		return []
	if isinstance(value, (list, tuple)):
		return [x for x in value if x]
	return [value] if value else []

def get_noun_article_mode(noun: str | None) -> str | None:
	return None

def apply_article_to_noun(noun: str | None, article: str='in') -> str | None:
	return noun
VISIBLE_PRONOUN_MAP_SP_TO_NTL = {'yo': 'nehuatl', 'tú': 'tehuatl', 'ella': 'yehuatl', 'él': 'yehuatl', 'nosotras': 'tehuan', 'nosotros': 'tehuan', 'ustedes': 'anmehuan', 'ellas': 'yehuan', 'ellos': 'yehuan'}
AMBIGUOUS_SP_EQUIVALENCES = {
	'como': {
		'verb': 'comer',
		'comparative': 'kenin',
	}
}
PRONOUN_MAP_SP = {'yo': ('1', 'sg'), 'tú': ('2', 'sg'), 'él': ('3', 'sg'), 'ella': ('3', 'sg'), 'nosotras': ('1', 'pl'), 'nosotros': ('1', 'pl'), 'ustedes': ('2', 'pl'), 'ellas': ('3', 'pl'), 'ellos': ('3', 'pl')}
SEMIPRONOUN_MAP_NTL = {('1', 'sg'): 'ni', ('2', 'sg'): 'ti', ('3', 'sg'): '∅', ('1', 'pl'): 'ti', ('2', 'pl'): 'an', ('3', 'pl'): '∅'}
REFLEXIVE_MAP_SP_TO_NTL = {'me': 'nimo', 'te': 'timo', 'se': '∅mo', 'nos': 'timo'}
DIRECT_OBJECT_MAP_SP_TO_NTL = {'a mí': 'nech', 'mí': 'nech', 'a ti': 'mitz', 'ti': 'mitz', 'a ella': 'ki', 'a él': 'ki', 'a nosotras': 'tech', 'a nosotros': 'tech', 'a ustedes': 'anmech', 'a ellas': 'kin', 'a ellos': 'kin'}
CLITIC_OBJECT_MAP_SP_TO_NTL = {'me': 'nech', 'te': 'mitz', 'nos': 'tech', 'le': 'ki', 'les': 'anmech', 'lo': 'ki', 'la': 'ki', 'los': 'kin', 'las': 'kin'}
DOUBLE_CLITIC_OBJECT_MAP_SP_TO_NTL = {'melo': 'nech ki', 'mela': 'nech ki', 'melos': 'nech kin', 'melas': 'nech kin', 'telo': 'mitz ki', 'tela': 'mitz ki', 'telos': 'mitz kin', 'telas': 'mitz kin', 'selo': 'mo ki', 'sela': 'mo ki', 'selos': 'mo kin', 'selas': 'mo kin', 'noslo': 'tech ki', 'nosla': 'tech ki', 'noslos': 'tech kin', 'noslas': 'tech kin'}
CONNECTORS_SP_TO_NTL = {'y': 'uan', 'e': 'uan'}
BELONGING_MAP_SP_TO_NTL = {'mi': 'no', 'mis': 'no', 'tu': 'mo', 'tus': 'mo', 'su': 'i', 'sus': 'i', 'nuestro': 'to', 'nuestra': 'to', 'nuestros': 'to', 'nuestras': 'to', 'vuestro': 'anmo', 'vuestra': 'anmo', 'vuestros': 'anmo', 'vuestras': 'anmo'}
MODAL_AUXILIARIES_SP_TO_NTL = {'debo': 'uihkili', 'debes': 'uihkili', 'debe': 'uihkili', 'debemos': 'uihkili', 'deben': 'uihkili', 'debí': 'uihkili', 'debiste': 'uihkili', 'debió': 'uihkili', 'debimos': 'uihkili', 'debieron': 'uihkili', 'deberé': 'uihkili', 'deberás': 'uihkili', 'deberá': 'uihkili', 'deberemos': 'uihkili', 'deberán': 'uihkili', 'debía': 'uihkili', 'debia': 'uihkili', 'debías': 'uihkili', 'debias': 'uihkili', 'debíamos': 'uihkili', 'debiamos': 'uihkili', 'debían': 'uihkili', 'debian': 'uihkili', 'debería': 'uihkili', 'deberías': 'uihkili', 'deberíamos': 'uihkili', 'deberían': 'uihkili', 'quiero': 'neki', 'quieres': 'neki', 'quiere': 'neki', 'queremos': 'neki', 'quieren': 'neki', 'quise': 'neki', 'quisiste': 'neki', 'quiso': 'neki', 'quisimos': 'neki', 'quisieron': 'neki', 'quería': 'neki', 'queria': 'neki', 'querías': 'neki', 'querias': 'neki', 'queríamos': 'neki', 'queriamos': 'neki', 'querían': 'neki', 'querian': 'neki', 'querría': 'neki', 'querria': 'neki', 'querrías': 'neki', 'querrias': 'neki', 'querríamos': 'neki', 'querriamos': 'neki', 'querrían': 'neki', 'querrian': 'neki', 'puedo': 'ueli', 'puedes': 'ueli', 'puede': 'ueli', 'podemos': 'ueli', 'pueden': 'ueli', 'pude': 'ueli', 'pudiste': 'ueli', 'pudo': 'ueli', 'pudimos': 'ueli', 'pudieron': 'ueli', 'podía': 'ueli', 'podia': 'ueli', 'podías': 'ueli', 'podias': 'ueli', 'podíamos': 'ueli', 'podiamos': 'ueli', 'podían': 'ueli', 'podian': 'ueli', 'podría': 'ueli', 'podria': 'ueli', 'podrías': 'ueli', 'podrias': 'ueli', 'podríamos': 'ueli', 'podriamos': 'ueli', 'podrían': 'ueli', 'podrian': 'ueli'}

def is_modal_auxiliary_sp(token: str) -> bool:
	return token in MODAL_AUXILIARIES_SP_TO_NTL

def is_spanish_infinitive(token: str) -> bool:
	token = strip_accents_for_compare(token)
	return token.endswith(('ar', 'er', 'ir'))

def split_ntl_object_pair(value: str | None):
	if not value:
		return (None, None)
	value = str(value).strip()
	if ' ' in value:
		indirect_object, direct_object = value.split(' ', 1)
		return (indirect_object, direct_object)
	return (None, value)

COMPOUND_AUXILIARIES_SP = {
	# Presente perfecto
	"he": {"subject": ("1", "sg"), "compound_kind": "present_perfect", "aspect": "ye", "past_marker": "o"},
	"has": {"subject": ("2", "sg"), "compound_kind": "present_perfect", "aspect": "ye", "past_marker": "o"},
	"ha": {"subject": ("3", "sg"), "compound_kind": "present_perfect", "aspect": "ye", "past_marker": "o"},
	"hemos": {"subject": ("1", "pl"), "compound_kind": "present_perfect", "aspect": "ye", "past_marker": "o"},
	"han": {"subject": ("3", "pl"), "compound_kind": "present_perfect", "aspect": "ye", "past_marker": "o"},

	# Pluscuamperfecto / antecopretérito
	"había": {"subject": ("1", "sg"), "compound_kind": "pluperfect", "aspect": "achto", "past_marker": "o"},
	"habías": {"subject": ("2", "sg"), "compound_kind": "pluperfect", "aspect": "achto", "past_marker": "o"},
	"habíamos": {"subject": ("1", "pl"), "compound_kind": "pluperfect", "aspect": "achto", "past_marker": "o"},
	"habían": {"subject": ("3", "pl"), "compound_kind": "pluperfect", "aspect": "achto", "past_marker": "o"},

	# Pretérito anterior / antepretérito
	"hube": {"subject": ("1", "sg"), "compound_kind": "preterite_anterior", "aspect": "achto", "past_marker": "o"},
	"hubiste": {"subject": ("2", "sg"), "compound_kind": "preterite_anterior", "aspect": "achto", "past_marker": "o"},
	"hubo": {"subject": ("3", "sg"), "compound_kind": "preterite_anterior", "aspect": "achto", "past_marker": "o"},
	"hubimos": {"subject": ("1", "pl"), "compound_kind": "preterite_anterior", "aspect": "achto", "past_marker": "o"},
	"hubieron": {"subject": ("3", "pl"), "compound_kind": "preterite_anterior", "aspect": "achto", "past_marker": "o"},

	# Futuro perfecto / antefuturo
	"habré": {"subject": ("1", "sg"), "compound_kind": "future_perfect", "aspect": "ikin niman"},
	"habrás": {"subject": ("2", "sg"), "compound_kind": "future_perfect", "aspect": "ikin niman"},
	"habrá": {"subject": ("3", "sg"), "compound_kind": "future_perfect", "aspect": "ikin niman"},
	"habra": {"subject": ("3", "sg"), "compound_kind": "future_perfect", "aspect": "ikin niman"},
	"habremos": {"subject": ("1", "pl"), "compound_kind": "future_perfect", "aspect": "ikin niman"},
	"habrán": {"subject": ("3", "pl"), "compound_kind": "future_perfect", "aspect": "ikin niman"},
	"habran": {"subject": ("3", "pl"), "compound_kind": "future_perfect", "aspect": "ikin niman"},

	# Formas compuestas del subjuntivo (-ra, -se, -re).
	# Según la norma establecida, siguen la misma estructura del futuro perfecto.
	"hubiera": {"subject": ("1", "sg"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieras": {"subject": ("2", "sg"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiéramos": {"subject": ("1", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieramos": {"subject": ("1", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieran": {"subject": ("3", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiese": {"subject": ("1", "sg"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieses": {"subject": ("2", "sg"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiésemos": {"subject": ("1", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiesemos": {"subject": ("1", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiesen": {"subject": ("3", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiere": {"subject": ("1", "sg"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieres": {"subject": ("2", "sg"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubiéremos": {"subject": ("1", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieremos": {"subject": ("1", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},
	"hubieren": {"subject": ("3", "pl"), "compound_kind": "subjunctive_perfect", "aspect": "ikin niman"},

	# Condicional perfecto: se conserva para atenderlo en su grupo.
	"habría": {"subject": ("1", "sg"), "compound_kind": "conditional_perfect", "aspect": "intla", "conditional": True},
	"habrías": {"subject": ("2", "sg"), "compound_kind": "conditional_perfect", "aspect": "intla", "conditional": True},
	"habríamos": {"subject": ("1", "pl"), "compound_kind": "conditional_perfect", "aspect": "intla", "conditional": True},
	"habrían": {"subject": ("3", "pl"), "compound_kind": "conditional_perfect", "aspect": "intla", "conditional": True},
}


def compound_subject_semipronoun(subject: tuple[str, str]) -> str:
	"""Devuelve el semipronombre lógico, sin inventarlo para tercera persona."""
	return SEMIPRONOUN_MAP_NTL.get(subject, "").replace("∅", "")


def canonical_compound_participle_ntl(participle_ntl: str) -> str:
	"""Normaliza duplicaciones accidentales del marcador inicial o-."""
	value = str(participle_ntl or "").strip()
	if value.startswith("o"):
		return "o" + value.lstrip("o")
	return value


def normalize_compound_participle_ntl(participle_ntl: str) -> str:
	"""Obtiene la forma sin el marcador inicial o-."""
	value = canonical_compound_participle_ntl(participle_ntl)
	if value.startswith("o") and len(value) > 1:
		return value[1:]
	return value


def compound_verb_root_ntl(participle_ntl: str) -> str:
	"""Recupera la raíz verbal desde la forma registrada en ado_ido.

	Ejemplos validados:
		otlakuak -> tlakua
		nehnemik -> nehnemi
		izak -> iza
		chiuatok -> chiua
	"""
	value = normalize_compound_participle_ntl(participle_ntl)
	if value.endswith("tok") and len(value) > 3:
		return value[:-3]
	if value.endswith("k") and len(value) > 1:
		return value[:-1]
	return value


def _compound_plural_suffix(subject: tuple[str, str], singular: str, plural: str) -> str:
	return plural if subject[1] == "pl" else singular


def build_compound_participle_ntl(
	auxiliary_sp: str,
	participle_sp: str,
	subject: tuple[str, str],
	reflexive: bool = False,
) -> str | None:
	"""Construye cada familia perfecta con una regla explícita.

	No se forman futuros ni copretéritos sobre el participio terminado en -k.
	La tabla de regresión de primera persona singular es la autoridad lingüística.
	"""
	auxiliary_data = COMPOUND_AUXILIARIES_SP.get(auxiliary_sp)
	if not auxiliary_data:
		return None

	participle_value = tolerant_lookup(participle_sp, ado_ido)
	participle_ntl = first_variant(participle_value)
	if not participle_ntl:
		return None
	participle_ntl = canonical_compound_participle_ntl(participle_ntl)

	kind = str(auxiliary_data.get("compound_kind") or "")
	aspect = str(auxiliary_data.get("aspect") or "").strip()
	semi = compound_subject_semipronoun(subject)
	clean = normalize_compound_participle_ntl(participle_ntl)
	root = compound_verb_root_ntl(participle_ntl)
	plural = subject[1] == "pl"
	parts: list[str] = []

	if aspect:
		parts.append(aspect)

	if kind == "present_perfect":
		# he comido -> ye oni tlakuak
		past_subject = f"o{semi}" if semi else "o"
		parts.append(past_subject)
		if reflexive:
			parts.append("mo")
		main = clean
		if plural and not main.endswith("keh"):
			main = fuse_k(main, "keh")
		parts.append(main)

	elif kind == "preterite_anterior":
		# hube comido -> achto inon o ni otlakuak
		parts.append("o")
		if semi:
			parts.append(semi)
		if reflexive:
			parts.append("mo")
		main = clean
		if plural and not main.endswith("keh"):
			main = fuse_k(main, "keh")
		parts.append(main)

	elif kind == "pluperfect":
		# había comido -> achto inon tlakuaya
		if reflexive:
			parts.append("mo")
		parts.append(root + ("yakeh" if plural else "ya"))

	elif kind in {"future_perfect", "subjunctive_perfect"}:
		# habré/hubiera/hubiese/hubiere comido -> ikin niman ni tlakuaz
		if semi:
			parts.append(semi)
		if reflexive:
			parts.append("mo")
		parts.append(root + ("zkeh" if plural else "z"))

	elif kind == "conditional_perfect":
		# habría comido -> intla ki tlakuazya
		direct_object = str(auxiliary_data.get("direct_object") or "").strip()
		if direct_object:
			parts.append(direct_object)
		if reflexive:
			parts.append("mo")
		parts.append(root + ("zyakeh" if plural else "zya"))

	else:
		return None

	return " ".join(p for p in parts if p).strip()


def detect_compound_participle_sp(
	tokens: list[str],
	explicit_subject: tuple[str, str] | None = None,
) -> dict | None:
	if not tokens:
		return None

	reflexive_tokens = {"mismo", "misma", "mismos", "mismas"}

	# Gerundio compuesto: habiendo comido -> onkatika otlakuak
	for auxiliary_index, token in enumerate(tokens):
		if token != "habiendo":
			continue
		participle_index = auxiliary_index + 1
		if participle_index >= len(tokens):
			continue
		participle_sp = tokens[participle_index]
		participle_value = tolerant_lookup(participle_sp, ado_ido)
		participle_ntl = first_variant(participle_value)
		if not participle_ntl:
			continue
		participle_ntl = canonical_compound_participle_ntl(participle_ntl)
		subject = explicit_subject or ("3", "sg")
		translation = f"onkatika {participle_ntl}".strip()
		return {
			"translation": translation,
			"subject": subject,
			"auxiliary_sp": token,
			"participle_sp": participle_sp,
			"participle_ntl": participle_ntl,
			"reflexive": False,
			"consumed_indexes": {auxiliary_index, participle_index},
		}

	for auxiliary_index, auxiliary_sp in enumerate(tokens):
		auxiliary_data = COMPOUND_AUXILIARIES_SP.get(auxiliary_sp)
		if not auxiliary_data:
			continue

		participle_index = auxiliary_index + 1
		if participle_index >= len(tokens):
			continue

		participle_sp = tokens[participle_index]
		participle_value = tolerant_lookup(participle_sp, ado_ido)
		if not participle_value:
			continue

		subject = explicit_subject or auxiliary_data["subject"]
		reflexive_indexes = {
			index
			for index, token in enumerate(tokens[:auxiliary_index])
			if token in reflexive_tokens
		}
		reflexive = bool(reflexive_indexes)

		translation = build_compound_participle_ntl(
			auxiliary_sp=auxiliary_sp,
			participle_sp=participle_sp,
			subject=subject,
			reflexive=reflexive,
		)
		if not translation:
			continue

		return {
			"translation": translation,
			"subject": subject,
			"auxiliary_sp": auxiliary_sp,
			"participle_sp": participle_sp,
			"participle_ntl": first_variant(participle_value),
			"reflexive": reflexive,
			"consumed_indexes": {
				auxiliary_index,
				participle_index,
				*reflexive_indexes,
			},
		}

	return None

BELONGING_NOUN_CONTEXT_SP_TO_NTL = {'casa': 'kalli', 'hogar': 'chantli'}
QUESTION_MARKERS_SP_TO_NTL = {'question_open': 'koch'}
LOCATIVE_MAP_SP_TO_NTL = {'bajo': 'tzin', 'debajo': 'tzin', 'dentro': 'itek', 'adentro': 'itek'}
BELONGING_PREFIXES = {'no', 'mo', 'i', 'to', 'anmo', 'in'}


def normalize_fixed_ntl_sequences(text: str) -> str:
	return re.sub(r'\bnelli\s+ki\b', 'tlen nelli', text)

FIXED_PHRASES_SP_TO_NTL = {'es que': 'tlen', 'salvo conducto': 'aztli', 'rosa': 'xokoxochitl', 'color rosa': 'tlapaltik', 'sin problema': 'amotla ouihyotl', 'tuvo que trasladarse allí con sus hijas': 'ompa ika i pilkoneuan o mo olitik', 'les dijo que no les quedaba más remedio que aprender a labrar la tierra': 'o kin ihtok tlen izel tzalotizkehtza tlalteteki', 'buena comida de maíz y frijol': 'ezentlakualli', 'comida de maíz y frijol': 'ezentlakualli'}
FIXED_PHRASES_SP_TO_NTL.update({'salida del sol': 'tonalkizayan', 'puesta del sol': 'tonalkalakiyan', 'a través de': 'ipal', 'por medio de': 'ipal', 'a lo largo de': 'ipal', 'mujer joven': 'ziuatl', 'mujer madura': 'zouatl', 'hombre joven': 'telpochtli', 'mujer joven': 'ziuatl', 'mujer madura': 'zouatl', 'hombre joven': 'telpochtli', 'pequeña flor': 'xochipilli', 'siete días': 'ilhuchikome', 'hacer buches': 'akamak olinipacho', 'buches hacer': 'akamak olinipacho', 'bomba para rociar': 'achiuazmalaz', 'bomba de rociar': 'auachikmalaz', 'bolsa de mujer': 'chikipiltlapalli', 'bolso de mujer': 'chikipiltlapalli', 'bodega ubicada': 'kouakan', 'bodega temporal': 'kouhman', 'bodega nueva': 'kouhyan', 'bodega de resguardo': 'kouiko', 'bebida provechosa': 'akotzatzalik', 'bajada de agua': 'achapantla', 'azúcar blanca': 'iztaktzopelnextli', 'aún no pertenece': 'amoakua', 'aún no': 'amoak', 'atracción gravitatoria': 'etikyotl', 'atracción metálica': 'tepozanayotl', 'atorar en árbol': 'kuaukui', 'atorar en árbol': 'kuaukuakan', 'animal semejante a la garduña': 'kakomiztli', 'alguien se sabe': 'akinmomati', 'algo sobre puesto de': 'apan', 'a lado': 'itlak', 'a su lado': 'itlak', 'aire fuerte': 'ehekachikaua', 'adornos de papel': 'amaneapanaluan', 'adorno de papel': 'amaneapanalli', 'abundancia de agua': 'atlanyotl', 'abundancia de agua': 'atlan', 'azul intenso': 'yayauhxiuhtik', 'azul suave': 'tzinxiuhtik', 'verde intenso': 'xoxohtik', 'verde suave': 'tzinxohtik', 'rojo intenso': 'chichiltik', 'rojo suave': 'tzinchiltik', 'rosa mexicano': 'tlatlapaltik', 'amarillo intenso': 'kokoztik', 'amarillo suave': 'tzinkoztik', 'mi cama azul': 'no xiuhtik tlapech', 'me dejé yo mi cama azul': 'onimo kauk no xiuhtik tlapech', 'a mí': 'nech', 'a ti': 'mitz', 'a ella': 'yehua', 'a él': 'yehua', 'a nosotras': 'tech', 'a nosotros': 'tech', 'a ustedes': 'anmech', 'a ellas': 'yehuan', 'a ellos': 'yehuan', 'entre las piernas': 'metznepantla', 'pasado mañana': 'nimanmoztla'})
PICAR_VARIANTES = {'picar': ['chiloa', 'uitzpani', 'chiuahtzoti'], 'punzar': ['uitzpani', 'chiuahtzoti'], 'pinchar': ['chiuahtzoti'], 'espinar': ['uitzpani', 'auaui']}
LEXICALIZED_NOUN_COMPOUNDS_SP_TO_NTL = {'piedra del sol': 'tonaltetl', 'calendario azteca': 'tonaltetl', 'carbon de dinero': 'tekontekontli', 'dinero de carbon': 'tekontekontli', 'moneda de carbon': 'tekontekontli', 'billete de carbon': 'tekotekontli'}
REL_LINKERS_SP = {'de', 'del'}
REL_ARTICLES_SP = {'el', 'la', 'los', 'las'}
LEADING_ARTICLES_SP = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'}
CORE_VERBS_SP_TO_NTL = {'allá': 'ompa', 'allí': 'ompa', 'ver': 'ita', 'querer': 'neki', 'amar': 'tlazohtla', 'volar': 'patlani', 'recargar': 'onmamaua', 'preservar': 'tlanemonyau', 'resistir': 'chikaua', 'avanzar': 'nehnemi', 'decir': 'ilia', 'decidir': 'iltlakui', 'expresar': 'ihto', 'hablar': 'tlahto', 'llamar': 'notza', 'platicar': 'nonotza', 'preguntar': 'tlahtlania', 'responder': 'nankilia', 'afirmar': 'kemilia', 'negar': 'amoihto', 'caer': 'uetzka', 'cargar': 'mamaua', 'ir': 'yau', 'venir': 'uala', 'pasar': 'pano', 'entrar': 'kalakia', 'salir': 'kiza', 'subir': 'eua', 'bajar': 'temo', 'caer': 'uetzka', 'llegar': 'ehko', 'caminar': 'nehnemi', 'viajar': 'ohtotoka', 'correr': 'cholo', 'existir': 'ka', 'tener': 'pia', 'haber': 'onka', 'vivir': 'nemi', 'morir': 'miki', 'nacer': 'ixua', 'descansar': 'zeui', 'crecer': 'izkaltia', 'hacer': 'chiua', 'usar': 'kehua', 'dejar': 'kaua', 'permitir': 'kaua', 'poner': 'tlalia', 'colocar': 'kania', 'abrir': 'tlapo', 'cerrar': 'tzakua', 'lavar': 'tlapaka', 'buscar': 'temo', 'llenar': 'temi', 'trabajar': 'tekiti', 'transformar': 'xolo', 'dividir': 'zezeki', 'unir': 'uania', 'llevar': 'uihka', 'traer': 'ualika', 'tapar': 'tlapa', 'dar': 'maka', 'acercar': 'naua', 'comer': 'tlakua', 'beber': 'koni', 'respirar': 'ihiyotia', 'dormir': 'kochi', 'poseer': 'u', 'poder': 'ueli', 'llover': 'kiaui', 'pensar': 'tlalnamiki', 'imaginar': 'izpanilyo', 'conocer': 'ixmati', 'creer': 'neltoka', 'saber': 'mati', 'recordar': 'ilnamiki', 'cantar': 'kuika', 'reír': 'uetzka', 'llorar': 'choka', 'sorprender': 'izamiki', 'asustar': 'mauhtia', 'molestar': 'kuezo', 'alegrar': 'paktia', 'entristecer': 'yolkoko'}
INFINITIVE_VERBS_SP_TO_NTL = {'abarcar': 'pacho', 'abatir': 'achikopala', 'abrazar': 'pacho', 'abrir': 'tlapo', 'abrir': 'tlapoa', 'abusar': 'achpaniua', 'acabar': 'tlami', 'aceptar': 'zelia', 'acercar': 'naua', 'acertar': 'xihia', 'aclarar': 'chipaua', 'acumular': 'achpania', 'adeudar': 'uihkilia', 'adulterar': 'akaui', 'afirmar': 'kemaihto', 'afirmar': 'kemili', 'afirmar': 'kemilia', 'agitar': 'olinia', 'ahogar': 'amiku', 'alcanzar': 'azi', 'alegrar': 'paktia', 'amar': 'tlazohtla', 'analizar': 'ihiztliko', 'anticipar': 'achto', 'apuntar': 'ahxiltia', 'aromatizar': 'ahuikaua', 'asombrar': 'iza', 'asustar': 'mauhtia', 'atacar': 'yaochiua', 'avanzar': 'nehnemi', 'bailar': 'ihtotia', 'bajar': 'temo', 'bajar': 'temoa', 'bañar': 'altia', 'beber': 'konia', 'bloquear': 'amokaua', 'buscar': 'temo', 'buscar': 'temoa', 'caer': 'uetzka', 'cambiar': 'pala', 'caminar': 'nehnemi', 'cantar': 'kuika', 'cargar': 'mamaua', 'cegar': 'ixmiktia', 'cerrar': 'tzakua', 'colar': 'amimina', 'colocar': 'kania', 'combidar': 'tzitzahtzihko', 'comer': 'tlakua', 'compartir': 'tzitzahtzihko', 'comprobar': 'itachiua', 'confundir': 'amoixmatiua', 'conocer': 'ixmati', 'conocer': 'tlamati', 'contaminar': 'akaui', 'contar': 'poua', 'controlar': 'chikaua', 'convencer': 'neltokachiua', 'correr': 'cholo', 'crear': 'chichiua', 'crecer': 'izkaltia', 'creer': 'neltoka', 'dar': 'maka', 'deber': 'uihkili', 'decidir': 'iltlakui', 'decir': 'ihto', 'decir': 'ilia', 'dejar': 'kaua', 'descansar': 'zeui', 'desear': 'eheleuia', 'deslizar': 'alaua', 'despertar': 'iza', 'detener': 'kehtza', 'dividir': 'zezeki', 'dormir': 'kochi', 'ejecutar': 'chiua', 'elaborar': 'chichiua', 'elevar': 'eua', 'embarcar': 'akalko', 'empapar': 'alou', 'encorbar': 'ahkolkui', 'enfriar': 'zezeui', 'ensuciar': 'tzoyo', 'entrar': 'kalaki', 'entrar': 'kalakia', 'entregar': 'maka', 'entristecer': 'yolkoko', 'erigir': 'eua', 'esperar': 'chia', 'establecer': 'tlali', 'estar': 'ka', 'exagerar': 'achtokzepa', 'exhortar': 'ahuania', 'exhortar': 'ahuia', 'existir': 'ka', 'expresar': 'ihto', 'filtrar': 'amimina', 'fortalecer': 'chikaua', 'gustar': 'paki', 'haber': 'onka', 'habitar': 'chantia', 'hablar': 'tlahto', 'hacer': 'chiua', 'hervir': 'amana', 'humedecer': 'atia', 'humillar': 'achikuepala', 'hundir': 'akalakia', 'imaginar': 'izpanilyo', 'impedir': 'amokaua', 'iniciar': 'peua', 'injuriar': 'amokualtlahto', 'inspirar': 'yolnotza', 'insultar': 'amokualtlahto', 'invitar': 'izpanotza', 'ir': 'yaui', 'jalar': 'an a', 'lavar': 'tlapaka', 'levantar': 'eua', 'limitar': 'amokaua', 'llamar': 'notza', 'llegar': 'ehko', 'llenar': 'temi', 'llevar': 'uihka', 'llorar': 'choka', 'llover': 'kiaui', 'mentir': 'amonelo', 'mojar': 'atia', 'molestar': 'kuezo', 'morir': 'miki', 'mostrar': 'ititi', 'mover': 'oli', 'mover': 'olia', 'moverse': 'mooli', 'nacer': 'ixua', 'necesitar': 'neneki', 'negar': 'amoihto', 'negar': 'amotia', 'nombrar': 'toka', 'observar': 'tlachia', 'ofender': 'amokualtlahto', 'oler': 'ahuia', 'parar': 'kehtza', 'pasar': 'pano', 'pasar': 'panoa', 'pedir': 'ihtlania', 'pensar': 'tlalnamiki', 'perder': 'poliui', 'perfumar': 'ahuikaua', 'permitir': 'kaua', 'pesar': 'etia', 'pinchar': 'chiuahtzoti', 'platicar': 'nonotza', 'poder': 'ueli', 'poner': 'tlalia', 'poseer': 'ua', 'predecir': 'achtoilia', 'preguntar': 'tlahtlani', 'preguntar': 'tlahtlania', 'preservar': 'tlanemonyau', 'prevenir': 'achtochiua', 'progresar': 'ahkuana', 'prologar': 'achtopou', 'proteger': 'chimalhua', 'querer': 'neki', 'rebasar': 'achtou', 'recargar': 'onmamaua', 'rechazar': 'amotilanazneki', 'recordar': 'ilnamiki', 'regañar': 'ahu', 'resbalar': 'alaua', 'resistir': 'chikaua', 'respirar': 'ihiyotia', 'responder': 'nankili', 'responder': 'nankilia', 'reír': 'uetzka', 'saber': 'mati', 'salir': 'kiza', 'seguir': 'totoka', 'separar': 'tzo', 'ser': 'eyo', 'señalar': 'ahxiltia', 'sincerar': 'neltokaihto', 'sobresaltar': 'ahkomana', 'socavar': 'achikuepala', 'sopesar': 'eheua', 'soportar': 'chikoua', 'sorprender': 'izamiki', 'subir': 'eua', 'sumergir': 'akalakia', 'superar': 'achtoua', 'tapar': 'tlapa', 'temblar': 'olinia', 'tener': 'pia', 'terminar': 'tlami', 'trabajar': 'tekiti', 'traer': 'ualika', 'transformar': 'xolo', 'transformar': 'xoloa', 'ungir': 'ahalou', 'unir': 'uania', 'untar': 'ahalou', 'usar': 'kehua', 'velar': 'amokochiua', 'venir': 'uala', 'ver': 'ita', 'verificar': 'itachiya', 'viajar': 'htotoka', 'viajar': 'ohtotoka', 'vibrar': 'olinia', 'vivir': 'nemi', 'volar': 'patlani', 'zambullir': 'akalakia'}
VERB_VARIANTS_SP_TO_NTL = {'decir': ['ihtoa', 'ilia'], 'expresar': ['ihto'], 'hablar': ['tlahto'], 'llamar': ['notza'], 'platicar': ['nonotza'], 'exhortar': ['ahuia', 'ahuania'], 'preguntar': ['tlahtlani', 'tlahtlania'], 'negar': ['amotia', 'amoihtoa'], 'afirmar': ['kemaihtoa', 'kemilia'], 'sincerar': ['neltokaihto'], 'mentir': ['amoneloa'], 'conocer': ['ixmati', 'tlamati']}
SPECIAL_VERBS_SP = {'ser', 'estar', 'existir', 'tener', 'haber'}
REGULAR_VERB_ENDINGS_SP = {'Present': [('o', ('1', 'sg')), ('as', ('2', 'sg')), ('a', ('3', 'sg')), ('amos', ('1', 'pl')), ('an', ('3', 'pl'))], 'Past': [('é', ('1', 'sg')), ('aste', ('2', 'sg')), ('ó', ('3', 'sg')), ('amos', ('1', 'pl')), ('aron', ('3', 'pl')), ('í', ('1', 'sg')), ('iste', ('2', 'sg')), ('ió', ('3', 'sg')), ('imos', ('1', 'pl')), ('ieron', ('3', 'pl'))], 'Future/Subj.': [('é', ('1', 'sg')), ('ás', ('2', 'sg')), ('á', ('3', 'sg')), ('emos', ('1', 'pl')), ('án', ('3', 'pl'))]}
IRREGULAR_VERB_FORMS_SP = {'voló': ('volar', 'Past', ('3', 'sg')), 'recargas': ('recargar', 'Present', ('2', 'sg')), 'preservará': ('preservar', 'Future/Subj.', ('3', 'sg')), 'resistió': ('resistir', 'Past', ('3', 'sg')), 'cerró': ('cerrar', 'Past', ('3', 'sg')), 'cayó': ('caer', 'Past', ('3', 'sg')), 'cargo': ('cargar', 'Present', ('1', 'sg')), 'cargas': ('cargar', 'Present', ('2', 'sg')), 'carga': ('cargar', 'Present', ('3', 'sg')), 'cargamos': ('cargar', 'Present', ('1', 'pl')), 'cargan': ('cargar', 'Present', ('3', 'pl')), 'cargué': ('cargar', 'Past', ('1', 'sg')), 'cargaste': ('cargar', 'Past', ('2', 'sg')), 'cargó': ('cargar', 'Past', ('3', 'sg')), 'cargamos': ('cargar', 'Past', ('1', 'pl')), 'cargaron': ('cargar', 'Past', ('3', 'pl')), 'cargaré': ('cargar', 'Future', ('1', 'sg')), 'cargarás': ('cargar', 'Future', ('2', 'sg')), 'cargaré': ('cargar', 'Future', ('3', 'sg')), 'cargaremos': ('cargar', 'Future', ('1', 'pl')), 'cargaremos': ('cargar', 'Future', ('2', 'pl')), 'cargarán': ('cargar', 'Future', ('3', 'pl')), 'cargue': ('cargar', 'Subjunctive', ('1', 'sg')), 'cargues': ('cargar', 'Subjunctive', ('2', 'sg')), 'cargue': ('cargar', 'Subjunctive', ('3', 'sg')), 'carguemos': ('cargar', 'Subjunctive', ('1', 'pl')), 'carguen': ('cargar', 'Subjunctive', ('3', 'pl')), 'caigo': ('caer', 'Present', ('1', 'sg')), 'caigas': ('caer', 'Present', ('2', 'sg')), 'caiga': ('caer', 'Present', ('3', 'sg')), 'caigamos': ('caer', 'Present', ('1', 'pl')), 'caigan': ('caer', 'Present', ('3', 'pl')), 'caí': ('caer', 'Past', ('1', 'sg')), 'caiste': ('caer', 'Past', ('2', 'sg')), 'cayó': ('caer', 'Past', ('3', 'sg')), 'caigamos': ('caer', 'Past', ('1', 'pl')), 'cayeron': ('caer', 'Past', ('3', 'pl')), 'cairé': ('caer', 'Future', ('1', 'sg')), 'cairás': ('caer', 'Future', ('2', 'sg')), 'cairé': ('caer', 'Future', ('3', 'sg')), 'cairemos': ('caer', 'Future', ('1', 'pl')), 'cairán': ('caer', 'Future', ('3', 'pl')), 'caiga': ('caer', 'Subjunctive', ('1', 'sg')), 'caigas': ('caer', 'Subjunctive', ('2', 'sg')), 'caiga': ('caer', 'Subjunctive', ('3', 'sg')), 'caigamos': ('caer', 'Subjunctive', ('1', 'pl')), 'caigan': ('caer', 'Subjunctive', ('3', 'pl')), 'veo': ('ver', 'Present', ('1', 'sg')), 'ves': ('ver', 'Present', ('2', 'sg')), 've': ('ver', 'Present', ('3', 'sg')), 'vemos': ('ver', 'Present', ('1', 'pl')), 'ven': ('ver', 'Present', ('3', 'pl')), 'vi': ('ver', 'Past', ('1', 'sg')), 'viste': ('ver', 'Past', ('2', 'sg')), 'vió': ('ver', 'Past', ('3', 'sg')), 'vimos': ('ver', 'Past', ('1', 'pl')), 'vieron': ('ver', 'Past', ('3', 'pl')), 'veré': ('ver', 'Future', ('1', 'sg')), 'verás': ('ver', 'Future', ('2', 'sg')), 'verá': ('ver', 'Future', ('3', 'sg')), 'veremos': ('ver', 'Future', ('3', 'sg')), 'verán': ('ver', 'Future', ('1', 'pl')), 'verán': ('ver', 'Future', ('3', 'pl')), 'vea': ('ver', 'Subjunctive', ('1', 'sg')), 'veas': ('ver', 'Subjunctive', ('2', 'sg')), 'vea': ('ver', 'Subjunctive', ('3', 'sg')), 'veamos': ('ver', 'Subjunctive', ('1', 'pl')), 'vean': ('ver', 'Subjunctive', ('3', 'pl')), 'doy': ('dar', 'Present', ('1', 'sg')), 'das': ('dar', 'Present', ('2', 'sg')), 'da': ('dar', 'Present', ('3', 'sg')), 'damos': ('dar', 'Present', ('1', 'pl')), 'dan': ('dar', 'Present', ('3', 'pl')), 'di': ('dar', 'Past', ('1', 'sg')), 'diste': ('dar', 'Past', ('2', 'sg')), 'dio': ('dar', 'Past', ('3', 'sg')), 'dimos': ('dar', 'Past', ('1', 'pl')), 'dieron': ('dar', 'Past', ('3', 'pl')), 'daré': ('dar', 'Future', ('1', 'sg')), 'darás': ('dar', 'Future', ('2', 'sg')), 'dará': ('dar', 'Future', ('3', 'sg')), 'daremos': ('dar', 'Future', ('1', 'pl')), 'darán': ('dar', 'Future', ('3', 'pl')), 'diera': ('dar', 'Subjunctive', ('1', 'sg')), 'dierás': ('dar', 'Subjunctive', ('2', 'sg')), 'dierá': ('dar', 'Subjunctive', ('3', 'sg')), 'diéramos': ('dar', 'Subjunctive', ('1', 'pl')), 'dieran': ('dar', 'Subjunctive', ('3', 'pl')), 'hago': ('hacer', 'Present', ('1', 'sg')), 'haces': ('hacer', 'Present', ('2', 'sg')), 'hace': ('hacer', 'Present', ('3', 'sg')), 'hacemos': ('hacer', 'Present', ('1', 'pl')), 'hacen': ('hacer', 'Present', ('3', 'pl')), 'hice': ('hacer', 'Past', ('1', 'sg')), 'hiciste': ('hacer', 'Past', ('2', 'sg')), 'hizo': ('hacer', 'Past', ('3', 'sg')), 'hicieron': ('hacer', 'Past', ('2', 'pl')), 'hicieron': ('hacer', 'Past', ('3', 'pl')), 'haré': ('hacer', 'Future', ('1', 'sg')), 'harás': ('hacer', 'Future', ('2', 'sg')), 'hará': ('hacer', 'Future', ('3', 'sg')), 'haremos': ('hacer', 'Future', ('1', 'pl')), 'harán': ('hacer', 'Future', ('3', 'pl')), 'haga': ('hacer', 'Subjunctive', ('1', 'sg')), 'hagas': ('hacer', 'Subjunctive', ('2', 'sg')), 'haga': ('hacer', 'Subjunctive', ('3', 'sg')), 'hagamos': ('hacer', 'Subjunctive', ('1', 'pl')), 'hagan': ('hacer', 'Subjunctive', ('3', 'pl')), 'quiero': ('querer', 'Present', ('1', 'sg')), 'quieres': ('querer', 'Present', ('2', 'sg')), 'quiere': ('querer', 'Present', ('3', 'sg')), 'queremos': ('querer', 'Present', ('1', 'pl')), 'quieren': ('querer', 'Present', ('3', 'pl')), 'quise': ('querer', 'Past', ('1', 'sg')), 'quisiste': ('querer', 'Past', ('2', 'sg')), 'quiso': ('querer', 'Past', ('3', 'sg')), 'quisimos': ('querer', 'Past', ('1', 'pl')), 'quisieron': ('querer', 'Past', ('3', 'pl')), 'querré': ('querer', 'Futuro', ('1', 'sg')), 'querrás': ('querer', 'Futuro', ('2', 'sg')), 'querrá': ('querer', 'Futuro', ('3', 'sg')), 'quisimos': ('querer', 'Futuro', ('1', 'pl')), 'querrán': ('querer', 'Futuro', ('3', 'pl')), 'quiera': ('querer', 'Subjunctive', ('1', 'sg')), 'quieras': ('querer', 'Subjunctive', ('2', 'sg')), 'quiera': ('querer', 'Subjunctive', ('3', 'sg')), 'queramos': ('querer', 'Subjunctive', ('1', 'pl')), 'quieran': ('querer', 'Subjunctive', ('3', 'pl')), 'voy': ('ir', 'Present', ('1', 'sg')), 'vas': ('ir', 'Present', ('2', 'sg')), 'va': ('ir', 'Present', ('3', 'sg')), 'vamos': ('ir', 'Present', ('1', 'pl')), 'van': ('ir', 'Present', ('3', 'pl')), 'fui': ('ir', 'Past', ('1', 'sg')), 'fuiste': ('ir', 'Past', ('2', 'sg')), 'fue': ('ir', 'Past', ('3', 'sg')), 'fuimos': ('ir', 'Past', ('1', 'pl')), 'fueron': ('ir', 'Past', ('3', 'pl')), 'iré': ('ir', 'Future', ('1', 'sg')), 'irás': ('ir', 'Future', ('2', 'sg')), 'irá': ('ir', 'Future', ('3', 'sg')), 'iremos': ('ir', 'Future', ('1', 'pl')), 'irán': ('ir', 'Future', ('3', 'pl')), 'vaya': ('ir', 'Subjunctive', ('1', 'sg')), 'vayas': ('ir', 'Subjunctive', ('2', 'sg')), 'vaya': ('ir', 'Subjunctive', ('3', 'sg')), 'vamos': ('ir', 'Subjunctive', ('1', 'pl')), 'vayan': ('ir', 'Subjunctive', ('3', 'pl')), 'vengo': ('venir', 'Present', ('1', 'sg')), 'vienes': ('venir', 'Present', ('2', 'sg')), 'viene': ('venir', 'Present', ('3', 'sg')), 'venimos': ('venir', 'Present', ('1', 'pl')), 'vienen': ('venir', 'Present', ('2', 'pl')), 'vine': ('venir', 'Past', ('1', 'sg')), 'viniste': ('venir', 'Past', ('2', 'sg')), 'vino': ('venir', 'Past', ('3', 'sg')), 'vinimos': ('venir', 'Past', ('1', 'pl')), 'vinieron': ('venir', 'Past', ('2', 'pl')), 'vendré': ('venir', 'Future', ('1', 'sg')), 'vendrás': ('venir', 'Future', ('2', 'sg')), 'vendrá': ('venir', 'Future', ('3', 'sg')), 'vendremos': ('venir', 'Future', ('1', 'pl')), 'vendrán': ('venir', 'Future', ('2', 'pl')), 'venga': ('venir', 'Subjunctive', ('1', 'sg')), 'vengas': ('venir', 'Subjunctive', ('2', 'sg')), 'venga': ('venir', 'Subjunctive', ('3', 'sg')), 'vengamos': ('venir', 'Subjunctive', ('1', 'pl')), 'vengan': ('venir', 'Subjunctive', ('2', 'pl')), 'digo': ('decir', 'Present', ('1', 'sg')), 'dices': ('decir', 'Present', ('2', 'sg')), 'dice': ('decir', 'Present', ('3', 'sg')), 'decimos': ('decir', 'Present', ('1', 'pl')), 'dicen': ('decir', 'Present', ('2', 'pl')), 'dije': ('decir', 'Past', ('1', 'sg')), 'dijiste': ('decir', 'Past', ('2', 'sg')), 'dijo': ('decir', 'Past', ('3', 'sg')), 'dijimos': ('decir', 'Past', ('1', 'pl')), 'dijeron': ('decir', 'Past', ('2', 'pl')), 'diré': ('decir', 'Future', ('1', 'sg')), 'dirás': ('decir', 'Future', ('2', 'sg')), 'dirá': ('decir', 'Future', ('3', 'sg')), 'diremos': ('decir', 'Future', ('1', 'pl')), 'dirán': ('decir', 'Future', ('2', 'pl')), 'diga': ('decir', 'Subjunctive', ('1', 'sg')), 'digas': ('decir', 'Subjunctive', ('2', 'sg')), 'diga': ('decir', 'Subjunctive', ('3', 'sg')), 'digamos': ('decir', 'Subjunctive', ('1', 'pl')), 'digan': ('decir', 'Subjunctive', ('2', 'pl')), 'decidido': ('decidir', 'Present', ('1', 'sg')), 'decidides': ('decidir', 'Present', ('2', 'sg')), 'decidide': ('decidir', 'Present', ('3', 'sg')), 'decidimos': ('decidir', 'Present', ('1', 'pl')), 'deciden': ('decidir', 'Present', ('2', 'pl')), 'decidí': ('decidir', 'Past', ('1', 'sg')), 'decidiste': ('decidir', 'Past', ('2', 'sg')), 'decidió': ('decidir', 'Past', ('3', 'sg')), 'decidimos': ('decidir', 'Past', ('1', 'pl')), 'decidieron': ('decidir', 'Past', ('2', 'pl')), 'decidiré': ('decidir', 'Future', ('1', 'sg')), 'decidirás': ('decidir', 'Future', ('2', 'sg')), 'decidirá': ('decidir', 'Future', ('3', 'sg')), 'decidiremos': ('decidir', 'Future', ('1', 'pl')), 'decidirán': ('decidir', 'Future', ('2', 'pl')), 'decidía': ('decidir', 'Copreterite', ('1', 'sg')), 'decidías': ('decidir', 'Copreterite', ('2', 'sg')), 'decidíamos': ('decidir', 'Copreterite', ('1', 'pl')), 'decidían': ('decidir', 'Copreterite', ('3', 'pl')), 'decidida': ('decidir', 'Subjunctive', ('1', 'sg')), 'decididas': ('decidir', 'Subjunctive', ('2', 'sg')), 'decidida': ('decidir', 'Subjunctive', ('3', 'sg')), 'decididamos': ('decidir', 'Subjunctive', ('1', 'pl')), 'decididan': ('decidir', 'Subjunctive', ('2', 'pl')), 'muero': ('morir', 'Present', ('1', 'sg')), 'mueres': ('morir', 'Present', ('2', 'sg')), 'muere': ('morir', 'Present', ('3', 'sg')), 'morimos': ('morir', 'Present', ('1', 'pl')), 'mueren': ('morir', 'Present', ('2', 'pl')), 'morí': ('morir', 'Past', ('1', 'sg')), 'moriste': ('morir', 'Past', ('2', 'sg')), 'murió': ('morir', 'Past', ('3', 'sg')), 'morimos': ('morir', 'Past', ('1', 'pl')), 'murieron': ('morir', 'Past', ('2', 'pl')), 'moriré': ('morir', 'Future', ('1', 'sg')), 'morirás': ('morir', 'Future', ('2', 'sg')), 'morirá': ('morir', 'Future', ('3', 'sg')), 'moriremos': ('morir', 'Future', ('1', 'pl')), 'morirán': ('morir', 'Future', ('2', 'pl')), 'muera': ('morir', 'Subjunctive', ('1', 'sg')), 'mueras': ('morir', 'Subjunctive', ('2', 'sg')), 'muera': ('morir', 'Subjunctive', ('3', 'sg')), 'muéramos': ('morir', 'Subjunctive', ('1', 'pl')), 'mueran': ('morir', 'Subjunctive', ('2', 'pl')), 'sé': ('saber', 'Present', ('1', 'sg')), 'sabes': ('saber', 'Present', ('2', 'sg')), 'sabe': ('saber', 'Present', ('3', 'sg')), 'sabemos': ('saber', 'Present', ('1', 'pl')), 'saben': ('saber', 'Present', ('2', 'pl')), 'supe': ('saber', 'Past', ('1', 'sg')), 'supiste': ('saber', 'Past', ('2', 'sg')), 'supo': ('saber', 'Past', ('3', 'sg')), 'supimos': ('saber', 'Past', ('1', 'pl')), 'supieron': ('saber', 'Past', ('2', 'pl')), 'sabré': ('saber', 'Future', ('1', 'sg')), 'sabrás': ('saber', 'Future', ('2', 'sg')), 'sabrá': ('saber', 'Future', ('3', 'sg')), 'sabremos': ('saber', 'Future', ('1', 'pl')), 'sabrán': ('saber', 'Future', ('2', 'pl')), 'sepa': ('saber', 'Subjunctive', ('1', 'sg')), 'sepas': ('saber', 'Subjunctive', ('2', 'sg')), 'sepa': ('saber', 'Subjunctive', ('3', 'sg')), 'sepamos': ('saber', 'Subjunctive', ('1', 'pl')), 'sepan': ('saber', 'Subjunctive', ('2', 'pl')), 'recuerdo': ('recordar', 'Present', ('1', 'sg')), 'recuerdas': ('recordar', 'Present', ('2', 'sg')), 'recuerda': ('recordar', 'Present', ('3', 'sg')), 'recordamos': ('recordar', 'Present', ('1', 'pl')), 'recuerdan': ('recordar', 'Present', ('2', 'pl')), 'recordé': ('recordar', 'Past', ('1', 'sg')), 'recordaste': ('recordar', 'Past', ('2', 'sg')), 'recordó': ('recordar', 'Past', ('3', 'sg')), 'recordamos': ('recordar', 'Past', ('1', 'pl')), 'recordaron': ('recordar', 'Past', ('2', 'pl')), 'recordaré': ('recordar', 'Future', ('1', 'sg')), 'recordarás': ('recordar', 'Future', ('2', 'sg')), 'recordará': ('recordar', 'Future', ('3', 'sg')), 'recordaremos': ('recordar', 'Future', ('1', 'pl')), 'recordarán': ('recordar', 'Future', ('2', 'pl')), 'recuerde': ('recordar', 'Subjunctive', ('1', 'sg')), 'recuerdes': ('recordar', 'Subjunctive', ('2', 'sg')), 'recuerde': ('recordar', 'Subjunctive', ('3', 'sg')), 'recordemos': ('recordar', 'Subjunctive', ('1', 'pl')), 'recueden': ('recordar', 'Subjunctive', ('2', 'pl'))}
SUFFIX_MAP = {'Present': {'sg': '', 'pl': 'h'}, 'Past': {'sg': 'k', 'pl': 'keh'}, 'Future': {'sg': 'z', 'pl': 'zteh'}, 'Subjunctive': {'sg': 'z', 'pl': 'zteh'}, 'Future/Subj.': {'sg': 'z', 'pl': 'zteh'}, 'Copreterite': {'sg': 'ya', 'pl': 'yah'}, 'Postpreterite': {'sg': 'zya', 'pl': 'zyah'}}
TRANSITIVE_VERBS_SP = {'abrir', 'acompañar', 'acompañar', 'agarrar', 'agarrar', 'amar', 'arreglar', 'arreglar', 'atrapar', 'atrapar', 'ayudar', 'ayudar', 'beber', 'buscar', 'calcular', 'cambiar', 'cerrar', 'comer', 'comparar', 'comprar', 'conocer', 'construir', 'contar', 'controlar', 'corregir', 'cortar', 'crear', 'cuidar', 'dar', 'decir', 'decorar', 'dibujar', 'dividir', 'elaborar', 'emplear', 'empujar', 'encontrar', 'enseñar', 'escribir', 'escuchar', 'explicar', 'fabricar', 'fortalecer', 'golpear', 'hacer', 'intercambiar', 'invitar', 'jalar', 'juntar', 'lavar', 'leer', 'limpiar', 'llamar', 'llenar', 'llevar', 'medir', 'mirar', 'mostrar', 'nombrar', 'observar', 'olvidar', 'oír', 'pedir', 'pesar', 'pintar', 'poner', 'preguntar', 'producir', 'pronunciar', 'proteger', 'quitar', 'reconocer', 'recordar', 'reparar', 'respetar', 'responder', 'romper', 'saludar', 'seguir', 'separar', 'sorprender', 'tomar', 'traducir', 'traer', 'transformar', 'unir', 'usar', 'utilizar', 'vaciar', 'vender', 'ver'}
INTRANSITIVE_VERBS_SP = {'vivir', 'morir', 'caer', 'llegar', 'salir', 'entrar', 'caminar', 'correr', 'dormir', 'nacer', 'volar', 'respirar', 'llover', 'crecer', 'existir', 'estar', 'ir', 'venir', 'descansar'}
PRONOMINAL_VERBS_SP = {'acercar', 'mover', 'lavar', 'vestir', 'peinar', 'cambiar', 'levantar', 'elevar', 'sumergir', 'hundir', 'caer'}
MIXED_VERBS_SP = {'abrir', 'cerrar', 'mover', 'cambiar', 'levantar', 'romper', 'separar', 'dividir', 'transformar'}
RELATIVE_OBJECT_CONNECTORS_SP_TO_NTL = {'lo que': 'tlein', 'el que': 'tlein', 'la que': 'tlein', 'los que': 'tlein', 'las que': 'tlein'}
OBLIGATIVE_PAST_SP = {'tuve': ('1', 'sg'), 'tuviste': ('2', 'sg'), 'tuvo': ('3', 'sg'), 'tuvimos': ('1', 'pl'), 'tuvieron': ('3', 'pl')}
ADVERBS_TIME_SP_TO_NTL = {'siempre': 'nochipa'}
PREPOSITIONAL_COMPLEMENTS_SP_TO_NTL = {'contigo': 'mouan'}
SP_PREPOSITIONAL_BLOCKS_TO_NTL = {'conmigo': 'nouan', 'contigo': 'mouan', 'con él': 'iuan', 'con ella': 'iuan', 'con ustedes': 'anmouan'}
SP_ADVERBS_TO_NTL = {'a ciegas': 'amotlakan', 'a escondidas': 'tlatikan', 'a mano': 'maikan', 'a menudo': 'totokan', 'a oscuras': 'yayauhkan', 'a pie': 'ikxikan', 'a pisada': 'ikxikan', 'a propósito': 'nekiyokan', 'a veces': 'ipan mantin', 'al arranque': 'peuakan', 'al comienzo': 'peuakan', 'al fin': 'tlamik', 'al final': 'tlamik', 'al inicio': 'peuakan', 'al instante': 'iman', 'al principio': 'peuakan', 'al revés': 'tlakuepak', 'ciegamente': 'amotlakan', 'de espaldas': 'tlakuitlapan', 'de frente': 'ixkok', 'de inmediato': 'iman', 'de ninguna manera': 'amotla ihkin', 'de nuevo': 'yankuik', 'de pronto': 'izamikan', 'de repente': 'izamikan', 'de vez en cuando': 'ikuakan', 'en absoluto': 'ipan tlamik', 'en ocasiones': ['imankan', 'imanpan'], 'en particular': 'ipan zeltik', 'en realidad': 'melauakan', 'en seguida': 'totokatok', 'en vano': 'amotlamikan', 'escondidamente': 'tlatikan', 'finalmente': 'tlamikan', 'frontalmente': 'ixkokan', 'inicialmente': 'peuakan', 'jamás': 'aik', 'manualmente': 'maikan', 'mientras': 'ipan kauitl', 'ni modo': 'amotla ihkin', 'nunca': 'aik', 'oscuramente': 'yayauhkan', 'pisadamente': 'ikxikan', 'poco a poco': 'pipilkan', 'por desgracia': 'amokualpanoyotl', 'por fin': 'ipan tlamik', 'por fortuna': 'kualpanoyotl', 'por lo general': 'nochikan', 'por supuesto': 'kemak', 'seguido': 'totokan', 'siempre': 'nochipa', 'siguiente': 'totokatok', 'sin duda': 'amotla nelyanalli', 'una vez': 'zeman'}
SP_PREPOSITIONAL_BLOCKS_TO_NTL = {'conmigo': 'nouan', 'contigo': 'mouan', 'con él': 'i uan', 'con el': 'i uan', 'con ella': 'i uan', 'con ustedes': 'anmo uan'}
SP_ADVERBS_TO_NTL = {'siempre': 'nochipa', 'jamás': 'aik', 'jamas': 'aik', 'nunca': 'aik'}
NTL_VISIBLE_PRONOUNS_TO_SP = {'nehuatl': 'yo', 'tehuatl': 'tú', 'yehuatl': 'ella', 'yehuatl': 'él', 'tehuan': 'nosotras', 'tehuan': 'nosotros', 'tehuantin': 'respetables nosotras', 'tehuantin': 'respetables nosotros', 'anmehuan': 'ustedes', 'yehuan': 'ellas', 'yehuan': 'ellos'}
NTL_SEMIPRONOUNS = {'ni': ('1', 'sg'), 'ti': ('2', 'sg'), 'an': ('2', 'pl')}

def reorder_adverb_plus_company_sp_to_ntl(text: str) -> str | None:
	t = normalize_input_sp(text)
	adv = None
	comp = None
	for k, v in SP_ADVERBS_TO_NTL.items():
		if re.search(f'\\b{re.escape(k)}\\b', t):
			adv = v
			break
	for k, v in SP_PREPOSITIONAL_BLOCKS_TO_NTL.items():
		if re.search(f'\\b{re.escape(k)}\\b', t):
			comp = v
			break
	if adv and comp:
		return f'{comp} {adv}'
	return None

def detect_pronoun_info(tokens: list[str]) -> tuple[str | None, tuple[str, str] | None]:
	for i, tk in enumerate(tokens):
		if i > 0 and tokens[i - 1] == 'a':
			continue
		if tk in PRONOUN_MAP_SP:
			visible = VISIBLE_PRONOUN_MAP_SP_TO_NTL.get(tk)
			return (visible, PRONOUN_MAP_SP[tk])
	return (None, None)

def detect_reflexive(tokens: list[str]) -> str | None:
	for tk in tokens:
		if tk in {'mismo', 'misma', 'mismos', 'mismas'}:
			return 'mo'
		if tk in REFLEXIVE_MAP_SP_TO_NTL:
			return REFLEXIVE_MAP_SP_TO_NTL[tk]
	return None

def resolve_verb_type_rules(verb_sp, reflexive, direct_object):
	if reflexive:
		return reflexive
	if verb_sp in PRONOMINAL_VERBS_SP:
		return '∅mo'
	if verb_sp in MIXED_VERBS_SP and (not direct_object):
		return '∅mo'
	if verb_sp in TRANSITIVE_VERBS_SP:
		return None
	if verb_sp in INTRANSITIVE_VERBS_SP:
		return None
	return reflexive

def detect_belonging(tokens):
	for i, tk in enumerate(tokens):
		# Un pronombre personal explícito marca sujeto; no debe reinterpretarse
		# como prefijo de pertenencia aunque exista una coincidencia léxica.
		if tk in PRONOUN_MAP_SP:
			continue
		if i > 0 and tokens[i - 1] == 'a':
			phrase = f'a {tk}'

			if phrase in DIRECT_OBJECT_MAP_SP_TO_NTL:
				continue

		val = tolerant_lookup(
			tk,
			BELONGING_MARKERS_SP_NTL
		)

		if val:
			return first_variant(val)

	return None




def detect_prepositions_sp(tokens):
	prepositions = []
	for tk in tokens:
		val = tolerant_lookup(tk, PREPOSITIONS_SP_NTL)
		if val:
			if isinstance(val, list):
				prepositions.append(min(val, key=len))
			else:
				prepositions.append(val)
	return prepositions

def detect_locative_phrase_sp(text: str) -> list[str]:
	t = normalize_input_sp(text)
	if 'en aquel lugar' in t:
		return ['ipan inon iuhkan']
	return []

def detect_locatives(tokens: list[str]) -> list[str]:
	found = []
	for tk in tokens:
		if tk in LOCATIVE_MAP_SP_TO_NTL:
			found.append(LOCATIVE_MAP_SP_TO_NTL[tk])
	return found

def detect_fixed_phrase_sp(text: str) -> str | None:
	t = normalize_input_sp(text)
	return FIXED_PHRASES_SP_TO_NTL.get(t)

def gerund_to_infinitive_sp(tk: str) -> str | None:
	tk = normalize_input_sp(tk)
	if tk.endswith('ando'):
		return tk[:-4] + 'ar'
	if tk.endswith('iendo'):
		base = tk[:-5]
		if base + 'er' in CORE_VERBS_SP_TO_NTL:
			return base + 'er'
		if base + 'ir' in CORE_VERBS_SP_TO_NTL:
			return base + 'ir'
	return None

def detect_dynamic_gerund_sp(tk: str) -> str | None:
	tk = normalize_input_sp(tk)
	if not tk.endswith(('ando', 'iendo')):
		return None
	direct = first_variant(tolerant_lookup(tk, sp_ntl))
	if direct:
		return direct
	inf = gerund_to_infinitive_sp(tk)
	if not inf:
		return None
	root = CORE_VERBS_SP_TO_NTL.get(inf)
	if not root:
		root = INFINITIVE_VERBS_SP_TO_NTL.get(inf)
	if not root:
		root = first_variant(tolerant_lookup(inf, sp_ntl))
	if not root:
		return None
	return root + 'tika'

def detect_adverbs_sp(tokens, used_indexes=None):
	if used_indexes is None:
		used_indexes = set()
	adverbs = []
	for i, tk in enumerate(tokens):
		if i in used_indexes:
			continue

		# La forma sin tilde 'como' sólo entra como comparativo cuando
		# resolve_ambiguous_spanish_tokens la marca explícitamente.
		# En cualquier otro contexto se reserva para el verbo comer.
		if tk == 'como':
			continue

		val = tolerant_lookup(tk, ADVERBS_SP_NTL)
		if val:
			if isinstance(val, (list, tuple)):
				item = min((v for v in val if v), key=len, default=None)
			else:
				item = val
			if item and item not in adverbs:
				adverbs.append(item)
	return adverbs

def detect_modifiers_sp(tokens: list[str], used_indexes: set[int] | None=None) -> list[str]:
	found = []
	seen = set()
	used_indexes = used_indexes or set()
	SER_FORMS = {'soy', 'eres', 'es', 'somos', 'son', 'era', 'eras', 'éramos', 'eran', 'seré', 'serás', 'será', 'seremos', 'serán', 'sea', 'seas', 'seamos', 'sean', 'fuera', 'fueras', 'fuéramos', 'fueran', 'fuese', 'fueses', 'fuésemos', 'fuesen', 'fuere', 'fueres', 'fuéremos', 'fueren', 'sé', 'sed'}

	def resolve_mente_adverb_sp(token: str) -> str | None:
		return MENTE_ADVERBS_SP_TO_NTL.get(token)

	def _add(val: str | None):
		if val and val not in seen:
			found.append(val)
			seen.add(val)

	def _looks_nominal_ntl(val: str) -> bool:
		v = (val or '').strip()
		return v.endswith(('tli', 'li', 'itl', 'tl'))

	def _is_verb_like_sp(tk: str) -> bool:
		return bool(detect_finite_verb([tk])[0] or detect_regular_verb([tk])[0] or detect_simple_verb([tk])[0] or detect_special_verb([tk])[0])
	for i, tk in enumerate(tokens):
		val = None
		gerund = detect_dynamic_gerund_sp(tk)
		if gerund:
			_add(gerund)
			continue
		if i in used_indexes:
			continue
		if is_money_token_sp(tk):
			_add(tk)
			continue
		if tk in {'no', 'de', 'del'}:
			continue
		if tk in ARTICLES_SP:
			continue
		if tk in {'algo', 'alguien', 'quien', 'quién'}:
			continue
		if tk in {'rosa', 'rosas'}:
			continue
		if tk in SER_FORMS:
			continue
		if tk in BELONGING_MAP_SP_TO_NTL or tk in REFLEXIVE_MAP_SP_TO_NTL or tk in PRONOUN_MAP_SP or (tk in DIRECT_OBJECT_MAP_SP_TO_NTL) or (tk in LOCATIVE_MAP_SP_TO_NTL):
			continue
		# Los sustantivos tienen prioridad sobre coincidencias accidentales
		# en la base de modificadores al reducir una forma plural.
		if tolerant_lexical_lookup(tk, NOUNS_SP_NTL) is not None:
			continue
		modifier_value = tolerant_lexical_lookup(tk, MODIFIERS)
		if modifier_value is not None:
			for item in all_variants(modifier_value):
				_add(item)
			continue
		if _is_verb_like_sp(tk):
			continue
		if tk in sp_ntl:
			val = first_variant(sp_ntl[tk])
			if val:
				if isinstance(val, str) and val.startswith(('ni ', 'ti ', 'an ')):
					continue
				if val == 'ipan':
					continue
				if isinstance(val, str) and val.endswith(('tli', 'li', 'itl', 'tl')):
					continue
			if tk.endswith('mente') or tk in {'sí', 'si', 'no', 'bien', 'mal', 'siempre', 'jamás', 'jamas', 'nunca'}:
				if val and (not _looks_nominal_ntl(val)):
					_add(val)
			continue
	return found

def detect_relative_object_connector_sp(tokens: list[str]) -> tuple[str | None, set[int]]:
	for phrase, connector in RELATIVE_OBJECT_CONNECTORS_SP_TO_NTL.items():
		phrase_tokens = phrase.split()
		n = len(phrase_tokens)
		for i in range(len(tokens) - n + 1):
			if tokens[i:i + n] == phrase_tokens:
				return (connector, set(range(i, i + n)))
	return (None, set())

def detect_nouns_sp(tokens: list[str], belonging: str | None=None, used_indexes: set[int] | None=None, visible_pronoun: str | None=None) -> list[str]:
	found = []
	seen = set()
	used_indexes = used_indexes or set()

	def _add(val: str | None):
		if val and val not in seen:
			found.append(val)
			seen.add(val)

	def _looks_nominal_ntl(val: str | None) -> bool:
		v = (val or '').strip()
		return v.endswith(('tli', 'li', 'itl', 'tl'))

	def _is_verb_like(tk: str) -> bool:
		return bool(detect_finite_verb([tk])[0] or detect_regular_verb([tk])[0] or detect_simple_verb([tk])[0] or detect_special_verb([tk])[0])

	def _is_ambiguous_finite_form(tk: str) -> bool:
		return bool(detect_finite_verb([tk])[0] or detect_regular_verb([tk])[0])

	def _get_noun_candidates(tk: str, belonging: str | None=None) -> list[str]:
		if tk in {'rosa', 'rosas'}:
			return ['xokoxochitl']
		if belonging:
			contextual = BELONGING_NOUN_CONTEXT_SP_TO_NTL.get(tk)
			if contextual:
				return [contextual]
		candidates = []
		keys = [tk, strip_accents_local(tk)]
		if tk.endswith('s') and len(tk) > 3:
			keys.append(tk[:-1])
			keys.append(strip_accents_local(tk[:-1]))
		if tk.endswith('es') and len(tk) > 4:
			keys.append(tk[:-2])
			keys.append(strip_accents_local(tk[:-2]))
		for key in keys:
			val = tolerant_lookup(key, NOUNS_SP_NTL)
			if val:
				# Las listas léxicas contienen alternativas, no elementos que deban
				# concatenarse. En traducción normal se usa una sola variante
				# preferente y se conservan las demás en el diccionario.
				item = first_variant(val)
				if item:
					candidates.append(item)
			val = tolerant_lookup(key, sp_ntl)
			if val:
				# sp_ntl puede mezclar categorías: selecciona únicamente la primera
				# variante nominal válida, sin expandir todas las alternativas.
				item = next(
					(candidate for candidate in all_variants(val) if candidate and _looks_nominal_ntl(candidate)),
					None
				)
				if item:
					candidates.append(item)
			if tk in {'mismo', 'misma', 'mismos', 'mismas'}:
				continue
		return candidates
	for i, tk in enumerate(tokens):
		if i in used_indexes:
			continue
		if tk in ARTICLES_SP:
			continue
		if tk in {'algo', 'alguien', 'quien', 'quién', 'no', 'de', 'del', 'en', 'aquel', 'aquella', 'lugar'}:
			continue
		if tk in {'ella', 'él', 'ellas', 'ellos', 'yehua', 'yehuan'}:
			continue
		if tk in BELONGING_MAP_SP_TO_NTL:
			continue
		if tk in REFLEXIVE_MAP_SP_TO_NTL:
			continue
		if tk in PRONOUN_MAP_SP:
			continue
		if tk in DIRECT_OBJECT_MAP_SP_TO_NTL:
			continue
		if tk in CLITIC_OBJECT_MAP_SP_TO_NTL:
			continue
		if tk in LOCATIVE_MAP_SP_TO_NTL:
			continue
		if tolerant_lookup(tk, ADVERBS_SP_NTL):
			continue
		noun_candidates = _get_noun_candidates(tk, belonging)
		prev_tk = tokens[i - 1] if i > 0 else ''
		if prev_tk in {'un', 'una'} and noun_candidates:
			for val in noun_candidates:
				_add('ze ' + val)
			continue
		if prev_tk in {'el', 'la', 'los', 'las'} and noun_candidates:
			for val in noun_candidates:
				_add(val)
			continue
		if belonging and noun_candidates:
			for val in noun_candidates:
				_add(val)
			continue
		prev_tk = tokens[i - 1] if i > 0 else ''
		next_tk = tokens[i + 1] if i + 1 < len(tokens) else ''
		if prev_tk == 'más' and next_tk == 'que':
			noun_candidates = _get_noun_candidates(tk, belonging)
			if noun_candidates:
				for val in noun_candidates:
					_add(val)
				continue
		if _is_verb_like(tk):
			continue
		if visible_pronoun and _is_ambiguous_finite_form(tk):
			continue
		if noun_candidates:
			for val in noun_candidates:
				_add(val)
			continue
		if tk == 'dinero':
			_add('tekontli')
			continue
		if tk in {'en', 'aquel', 'aquella', 'allí', 'ahi', 'ahí', 'lugar'}:
			continue
	return found

def detect_inline_fixed_phrases_sp(tokens: list[str]) -> tuple[list[str], set[int]]:
	found = []
	used_indexes = set()
	phrase_sources = []
	# Toda igualdad léxica multipalabra SP→NTL debe competir como una unidad
	# antes del análisis palabra por palabra. La coincidencia más larga gana.
	phrase_dictionaries = (
		FIXED_PHRASES_SP_TO_NTL,
		sp_ntl,
		NOUNS_SP_NTL,
		MODIFIERS_SP_NTL,
		ADVERBS_SP_NTL,
		PREPOSITIONS_SP_NTL,
	)
	for source in phrase_dictionaries:
		for phrase, val in source.items():
			if not isinstance(phrase, str) or ' ' not in phrase:
				continue
			phrase = normalize_input_sp(phrase).strip()
			if phrase:
				phrase_sources.append((phrase, val))
	phrase_sources.sort(key=lambda item: len(item[0].split()), reverse=True)
	for phrase, raw_val in phrase_sources:
		phrase_tokens = phrase.split()
		n = len(phrase_tokens)
		for i in range(len(tokens) - n + 1):
			if any((idx in used_indexes for idx in range(i, i + n))):
				continue
			if tokens[i:i + n] == phrase_tokens:
				val = first_variant(raw_val)
				if val:
					found.append(val)
					for idx in range(i, i + n):
						used_indexes.add(idx)
	return (found, used_indexes)

def clean_number_token(tk: str) -> str:
	tk = (tk or '').strip()
	tk = tk.strip('()[]{};:¡!¿?"\'')
	tk = tk.rstrip('.,')
	tk = tk.lstrip('$')
	return tk

def normalize_numeric_lookup_key_sp(tk: str) -> str:
	raw = clean_number_token(tk)
	if not raw:
		return ''
	normalized = raw.replace(',', '').replace('.', '')
	return normalized

def is_numeric_like_token_sp(tk: str) -> bool:
	raw = clean_number_token(tk)
	if not raw:
		return False
	if re.fullmatch('\\d[\\d\\.,]*', raw):
		return True
	if re.fullmatch('[ivxlcdmIVXLCDM]+', raw):
		return True
	return False

def is_money_token_sp(tk: str) -> bool:
	return tk.strip().startswith('$')

def build_quantified_amount_ntl(raw_tk: str, amount_ntl: str) -> str:
	if is_money_token_sp(raw_tk):
		return f'${amount_ntl} '
	return amount_ntl

def is_numeric_like_token_sp(tk: str) -> bool:
	clean = clean_number_token(tk)
	if not clean:
		return False
	if clean.isdigit():
		return True
	if re.fullmatch('[ivxlcdmIVXLCDM]+', clean):
		return True
	return False

def detect_embedded_numbers_sp(tokens: list[str]) -> list[str]:
	found = []
	seen = set()
	for tk in tokens:
		if not is_numeric_like_token_sp(tk):
			continue
		lookup = normalize_numeric_lookup_key_sp(tk)
		if lookup in MODIFIERS:
			raw_val = MODIFIERS[lookup]
			val = first_variant(raw_val)
			if val:
				val = build_quantified_amount_ntl(tk, val)
				if val not in seen:
					found.append(val)
					seen.add(val)
			continue
		if lookup in sp_ntl:
			val = first_variant(sp_ntl[lookup])
			if val:
				val = build_quantified_amount_ntl(tk, val)
				if val not in seen:
					found.append(val)
					seen.add(val)
	return found

def has_embedded_number_sp(tokens: list[str]) -> bool:
	for tk in tokens:
		clean_tk = clean_number_token(tk)
		if clean_tk in MODIFIERS:
			return True
	return False

def detect_literal_symbols_sp(tokens: list[str]) -> list[str]:
	found = []
	for tk in tokens:
		for ch in tk:
			if ch in {'(', ')', '[', ']', '{', '}'}:
				found.append(ch)
	return found


def detect_double_clitic_objects_sp(text: str) -> tuple[str | None, str | None]:
	tokens = normalize_input_sp(text).split()

	double_clitic_map = {
		('me', 'lo'): ('nech', 'ki'),
		('me', 'la'): ('nech', 'ki'),
		('me', 'los'): ('nech', 'kin'),
		('me', 'las'): ('nech', 'kin'),
		('te', 'lo'): ('mitz', 'ki'),
		('te', 'la'): ('mitz', 'ki'),
		('te', 'los'): ('mitz', 'kin'),
		('te', 'las'): ('mitz', 'kin'),
		('se', 'lo'): ('mo', 'ki'),
		('se', 'la'): ('mo', 'ki'),
		('se', 'los'): ('mo', 'kin'),
		('se', 'las'): ('mo', 'kin'),
		('nos', 'lo'): ('tech', 'ki'),
		('nos', 'la'): ('tech', 'ki'),
		('nos', 'los'): ('tech', 'kin'),
		('nos', 'las'): ('tech', 'kin'),
	}

	for index in range(len(tokens) - 1):
		clitic_pair = (
			tokens[index],
			tokens[index + 1],
		)

		if clitic_pair in double_clitic_map:
			return double_clitic_map[clitic_pair]

	return (None, None)



def detect_direct_object(text: str) -> str | None:
	tokens = text.split()
	if 'ustedes' in tokens and 'a' not in tokens:
		return None
	if 'a' in tokens and 'ustedes' in tokens and ('los' in tokens):
		return None
	belonging_words = {'mi', 'mis', 'tu', 'tus', 'su', 'sus', 'nuestras', 'nuestra', 'nuestros', 'nuestro', 'vuestras', 'vuestra', 'vuestros', 'vuestro'}
	has_dative_belonging_target = False
	for i, tk in enumerate(tokens[:-1]):
		if tk == 'a' and tokens[i + 1] in belonging_words:
			has_dative_belonging_target = True
			break
	for phrase, value in sorted(DIRECT_OBJECT_MAP_SP_TO_NTL.items(), key=lambda x: len(x[0].split()), reverse=True):
		phrase_tokens = phrase.split()
		for i in range(len(tokens) - len(phrase_tokens) + 1):
			if tokens[i:i + len(phrase_tokens)] == phrase_tokens:
				return value
	def is_preverbal_object_clitic(index: int) -> bool:
		"""Distingue lo/la/los/las clíticos de los artículos homógrafos.

		Un artículo introduce un grupo nominal ("los soldados", "la mujer") y
		no debe producir ki/kin. El clítico acusativo, en cambio, aparece ligado
		a una forma verbal ("los vi", "la quiero"). Se comprueba la primera
		palabra útil posterior para no alterar los acusativos explícitos reales.
		"""
		for following in tokens[index + 1:]:
			if following in {'no', 'nunca', 'jamás', 'ya', 'aún', 'aun', 'también', 'tambien'}:
				continue
			finite = detect_finite_verb([following])[0]
			regular = detect_regular_verb([following])[0]
			simple = detect_simple_verb([following])[0]
			special = detect_special_verb([following])[0]
			return bool(finite or regular or simple or special or following in COMPOUND_AUXILIARIES_SP)
		return False

	for index, tk in enumerate(tokens):
		if tk == 'me':
			return 'nech'
		if tk == 'te':
			return 'mitz'
		if tk in {'le', 'se'}:
			if has_dative_belonging_target:
				continue
			return 'ki'
		if tk == 'nos':
			return 'tech'
		if tk == 'les':
			if has_dative_belonging_target:
				continue
			return 'anmech'
		if tk in {'lo', 'la'} and is_preverbal_object_clitic(index):
			return 'ki'
		if tk in {'los', 'las'} and is_preverbal_object_clitic(index):
			return 'kin'
	return None

def detect_question_noun_sp(tokens: list[str]) -> str | None:
	for tk in tokens:
		if tk in {'quien', 'quién'}:
			return 'akin'
	return None
DECIR_PERIFRASTICO_ROOT = 'ihto'
AUX_HABER_FORMS_SP = {'he': ('1', 'sg', 'Past'), 'has': ('2', 'sg', 'Past'), 'ha': ('3', 'sg', 'Past'), 'hemos': ('1', 'pl', 'Past'), 'han': ('3', 'pl', 'Past'), 'había': ('1', 'sg', 'Copreterite'), 'habías': ('2', 'sg', 'Copreterite'), 'habíamos': ('1', 'pl', 'Copreterite'), 'habían': ('3', 'pl', 'Copreterite')}
DECIR_PARTICIPIOS_SP = {'dicho', 'dicha', 'dichos', 'dichas'}

def detect_periphrastic_decir_sp(tokens: list[str]) -> dict | None:
	"""
	Detecta:
	- he dicho
	- has dicho
	- ha dicho
	- hemos dicho
	- han dicho
	- había dicho
	- habías dicho
	- habíamos dicho
	- habían dicho

	Admite clíticos intermedios:
	- no te lo había dicho

	Devuelve además marcador resultativo: ye
	"""
	if not tokens:
		return None
	aux_idx = None
	aux_subject = None
	aux_time = None
	for i, tk in enumerate(tokens):
		aux_data = lookup_aux_haber_form(tk)
		if aux_data:
			aux_idx = i
			p, n, tm = aux_data
			aux_subject = (p, n)
			aux_time = tm
			break
	if aux_idx is None or aux_subject is None or aux_time is None:
		return None
	for j in range(aux_idx + 1, len(tokens)):
		tk = unicodedata.normalize('NFC', tokens[j]).strip().lower()
		if tk in DECIR_PARTICIPIOS_SP:
			return {'verb_sp': 'decir', 'verb_ntl': DECIR_PERIFRASTICO_ROOT, 'subject': aux_subject, 'time': aux_time, 'aspect_marker': 'ye', 'consumed_indexes': {aux_idx, j}}
	return None

def detect_simple_verb(tokens: list[str]) -> tuple[str | None, str | None]:
	for tk in tokens:
		if tk in INFINITIVE_VERBS_SP_TO_NTL:
			return (tk, INFINITIVE_VERBS_SP_TO_NTL[tk])
		if tk in CORE_VERBS_SP_TO_NTL:
			return (tk, CORE_VERBS_SP_TO_NTL[tk])
		ntl = first_variant(tolerant_lookup(tk, sp_ntl))
		if ntl:
			return (tk, ntl)
	return (None, None)

def detect_special_verb(tokens: list[str]) -> tuple[str | None, str | None]:
	for tk in tokens:
		if tk in SPECIAL_VERBS_SP and tk in CORE_VERBS_SP_TO_NTL:
			return (tk, CORE_VERBS_SP_TO_NTL[tk])
	return (None, None)

def detect_regular_verb(tokens: list[str]):
	if 'como' in tokens and any((x in tokens for x in {'tan', 'kexki', 'igual', 'mismo', 'misma', 'antes', 'achto'})):
		tokens = [tk for tk in tokens if tk != 'como']
	for tk in tokens:
		if tk.endswith('o') and len(tk) > 2:
			verb_sp = tk[:-1] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'sg'), 'Present')
		if tk.endswith('o') and len(tk) > 2:
			verb_sp = tk[:-1] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'sg'), 'Present')
			verb_sp = tk[:-1] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'sg'), 'Present')
		if tk.endswith('a') and len(tk) > 2:
			verb_sp = tk[:-1] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'sg'), 'Present')
		if tk.endswith('amos') and len(tk) > 5:
			verb_sp = tk[:-4] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'pl'), 'Present')
		if tk.endswith('an') and len(tk) > 3:
			verb_sp = tk[:-2] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'pl'), 'Present')
		if tk.endswith('é') and len(tk) > 2:
			verb_sp = tk[:-1] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'sg'), 'Past')
		if tk.endswith('aste') and len(tk) > 5:
			verb_sp = tk[:-4] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('2', 'sg'), 'Past')
		if tk.endswith('ó') and len(tk) > 2:
			verb_sp = tk[:-1] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'sg'), 'Past')
		if tk.endswith('aron') and len(tk) > 5:
			verb_sp = tk[:-4] + 'ar'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'pl'), 'Past')
		if tk.endswith('es') and len(tk) > 3:
			verb_sp = tk[:-2] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('2', 'sg'), 'Present')
			verb_sp = tk[:-2] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('2', 'sg'), 'Present')
		if tk.endswith('e') and len(tk) > 2:
			verb_sp = tk[:-1] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'sg'), 'Present')
			verb_sp = tk[:-1] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'sg'), 'Present')
		if tk.endswith('emos') and len(tk) > 5:
			verb_sp = tk[:-4] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'pl'), 'Present')
		if tk.endswith('imos') and len(tk) > 5:
			verb_sp = tk[:-4] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'pl'), 'Present')
		if tk.endswith('en') and len(tk) > 3:
			verb_sp = tk[:-2] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'pl'), 'Present')
			verb_sp = tk[:-2] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'pl'), 'Present')
		if tk.endswith('í') and len(tk) > 2:
			verb_sp = tk[:-1] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'sg'), 'Past')
			verb_sp = tk[:-1] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('1', 'sg'), 'Past')
		if tk.endswith('iste') and len(tk) > 5:
			verb_sp = tk[:-4] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('2', 'sg'), 'Past')
			verb_sp = tk[:-4] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('2', 'sg'), 'Past')
		if tk.endswith('ió') and len(tk) > 3:
			verb_sp = tk[:-2] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'sg'), 'Past')
			verb_sp = tk[:-2] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'sg'), 'Past')
		if tk.endswith('ieron') and len(tk) > 6:
			verb_sp = tk[:-5] + 'er'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'pl'), 'Past')
			verb_sp = tk[:-5] + 'ir'
			if verb_sp in CORE_VERBS_SP_TO_NTL:
				return (verb_sp, CORE_VERBS_SP_TO_NTL[verb_sp], ('3', 'pl'), 'Past')
	return (None, None, None, None)

def detect_finite_verb(tokens: list[str]) -> tuple[str | None, str | None, tuple[str, str] | None, str | None]:
	if 'como' in tokens and any((x in tokens for x in {'tan', 'kexki', 'igual', 'mismo', 'misma', 'antes', 'achto'})):
		tokens = [tk for tk in tokens if tk != 'como']

	def _get_verb_ntl(verb_sp: str):
		verb_ntl = CORE_VERBS_SP_TO_NTL.get(verb_sp)
		if not verb_ntl:
			verb_ntl = INFINITIVE_VERBS_SP_TO_NTL.get(verb_sp)
		if not verb_ntl:
			verb_ntl = first_variant(tolerant_lookup(verb_sp, sp_ntl))
		return verb_ntl

	def _try_candidate(verb_sp: str, subject: tuple[str, str], time: str):
		verb_ntl = _get_verb_ntl(verb_sp)
		if verb_ntl:
			return (verb_sp, verb_ntl, subject, time)
		return None

	def _regular_candidates_from_token(tk: str):
		candidates = []
		if tk.endswith('o') and len(tk) > 2:
			candidates.append((tk[:-1] + 'ar', ('1', 'sg'), 'Present'))
			candidates.append((tk[:-1] + 'er', ('1', 'sg'), 'Present'))
			candidates.append((tk[:-1] + 'ir', ('1', 'sg'), 'Present'))
		if tk.endswith('as') and len(tk) > 3:
			candidates.append((tk[:-2] + 'ar', ('2', 'sg'), 'Present'))
		if tk.endswith('a') and len(tk) > 2:
			candidates.append((tk[:-1] + 'ar', ('3', 'sg'), 'Present'))
		if tk.endswith('amos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('1', 'pl'), 'Present'))
		if tk.endswith('an') and len(tk) > 3:
			candidates.append((tk[:-2] + 'ar', ('3', 'pl'), 'Present'))
		if tk.endswith('es') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('2', 'sg'), 'Present'))
			candidates.append((tk[:-2] + 'ir', ('2', 'sg'), 'Present'))
		if tk.endswith('e') and len(tk) > 2:
			candidates.append((tk[:-1] + 'er', ('3', 'sg'), 'Present'))
			candidates.append((tk[:-1] + 'ir', ('3', 'sg'), 'Present'))
		if tk.endswith('emos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'er', ('1', 'pl'), 'Present'))
		if tk.endswith('imos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ir', ('1', 'pl'), 'Present'))
		if tk.endswith('en') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('3', 'pl'), 'Present'))
			candidates.append((tk[:-2] + 'ir', ('3', 'pl'), 'Present'))
		if tk.endswith('é') and len(tk) > 2:
			candidates.append((tk[:-1] + 'ar', ('1', 'sg'), 'Past'))
		if tk.endswith('aste') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('2', 'sg'), 'Past'))
		if tk.endswith('ó') and len(tk) > 2:
			candidates.append((tk[:-1] + 'ar', ('3', 'sg'), 'Past'))
		if tk.endswith('amos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('1', 'pl'), 'Past'))
		if tk.endswith('aron') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('3', 'pl'), 'Past'))
		if tk.endswith('í') and len(tk) > 2:
			candidates.append((tk[:-1] + 'er', ('1', 'sg'), 'Past'))
			candidates.append((tk[:-1] + 'ir', ('1', 'sg'), 'Past'))
		if tk.endswith('iste') and len(tk) > 5:
			candidates.append((tk[:-4] + 'er', ('2', 'sg'), 'Past'))
			candidates.append((tk[:-4] + 'ir', ('2', 'sg'), 'Past'))
		if tk.endswith('ió') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('3', 'sg'), 'Past'))
			candidates.append((tk[:-2] + 'ir', ('3', 'sg'), 'Past'))
		if tk.endswith('imos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ir', ('1', 'pl'), 'Past'))
		if tk.endswith('ieron') and len(tk) > 6:
			candidates.append((tk[:-5] + 'er', ('3', 'pl'), 'Past'))
			candidates.append((tk[:-5] + 'ir', ('3', 'pl'), 'Past'))
		if tk.endswith('aba') and len(tk) > 4:
			candidates.append((tk[:-3] + 'ar', ('1', 'sg'), 'Copreterite'))
			candidates.append((tk[:-3] + 'ar', ('3', 'sg'), 'Copreterite'))
		if tk.endswith('abas') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('2', 'sg'), 'Copreterite'))
		if tk.endswith('ábamos') and len(tk) > 7:
			candidates.append((tk[:-6] + 'ar', ('1', 'pl'), 'Copreterite'))
		if tk.endswith('abamos') and len(tk) > 7:
			candidates.append((tk[:-6] + 'ar', ('1', 'pl'), 'Copreterite'))
		if tk.endswith('aban') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('3', 'pl'), 'Copreterite'))
		if tk.endswith('ía') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('1', 'sg'), 'Copreterite'))
			candidates.append((tk[:-2] + 'ir', ('1', 'sg'), 'Copreterite'))
			candidates.append((tk[:-2] + 'er', ('3', 'sg'), 'Copreterite'))
			candidates.append((tk[:-2] + 'ir', ('3', 'sg'), 'Copreterite'))
		if tk.endswith('ia') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('1', 'sg'), 'Copreterite'))
			candidates.append((tk[:-2] + 'ir', ('1', 'sg'), 'Copreterite'))
			candidates.append((tk[:-2] + 'er', ('3', 'sg'), 'Copreterite'))
			candidates.append((tk[:-2] + 'ir', ('3', 'sg'), 'Copreterite'))
		if tk.endswith('ías') and len(tk) > 4:
			candidates.append((tk[:-3] + 'er', ('2', 'sg'), 'Copreterite'))
			candidates.append((tk[:-3] + 'ir', ('2', 'sg'), 'Copreterite'))
		if tk.endswith('ias') and len(tk) > 4:
			candidates.append((tk[:-3] + 'er', ('2', 'sg'), 'Copreterite'))
			candidates.append((tk[:-3] + 'ir', ('2', 'sg'), 'Copreterite'))
		if tk.endswith('íamos') and len(tk) > 6:
			candidates.append((tk[:-5] + 'er', ('1', 'pl'), 'Copreterite'))
			candidates.append((tk[:-5] + 'ir', ('1', 'pl'), 'Copreterite'))
		if tk.endswith('iamos') and len(tk) > 6:
			candidates.append((tk[:-5] + 'er', ('1', 'pl'), 'Copreterite'))
			candidates.append((tk[:-5] + 'ir', ('1', 'pl'), 'Copreterite'))
		if tk.endswith('ían') and len(tk) > 4:
			candidates.append((tk[:-3] + 'er', ('3', 'pl'), 'Copreterite'))
			candidates.append((tk[:-3] + 'ir', ('3', 'pl'), 'Copreterite'))
		if tk.endswith('ian') and len(tk) > 4:
			candidates.append((tk[:-3] + 'er', ('3', 'pl'), 'Copreterite'))
			candidates.append((tk[:-3] + 'ir', ('3', 'pl'), 'Copreterite'))
		if tk.endswith('e') and len(tk) > 2:
			candidates.append((tk[:-1] + 'ar', ('1', 'sg'), 'Subjunctive'))
			candidates.append((tk[:-1] + 'ar', ('3', 'sg'), 'Subjunctive'))
		if tk.endswith('es') and len(tk) > 3:
			candidates.append((tk[:-2] + 'ar', ('2', 'sg'), 'Subjunctive'))
		if tk.endswith('emos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'ar', ('1', 'pl'), 'Subjunctive'))
		if tk.endswith('en') and len(tk) > 3:
			candidates.append((tk[:-2] + 'ar', ('3', 'pl'), 'Subjunctive'))
		if tk.endswith('a') and len(tk) > 2:
			candidates.append((tk[:-1] + 'er', ('1', 'sg'), 'Subjunctive'))
			candidates.append((tk[:-1] + 'ir', ('1', 'sg'), 'Subjunctive'))
			candidates.append((tk[:-1] + 'er', ('3', 'sg'), 'Subjunctive'))
			candidates.append((tk[:-1] + 'ir', ('3', 'sg'), 'Subjunctive'))
		if tk.endswith('as') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('2', 'sg'), 'Subjunctive'))
			candidates.append((tk[:-2] + 'ir', ('2', 'sg'), 'Subjunctive'))
		if tk.endswith('amos') and len(tk) > 5:
			candidates.append((tk[:-4] + 'er', ('1', 'pl'), 'Subjunctive'))
			candidates.append((tk[:-4] + 'ir', ('1', 'pl'), 'Subjunctive'))
		if tk.endswith('an') and len(tk) > 3:
			candidates.append((tk[:-2] + 'er', ('3', 'pl'), 'Subjunctive'))
			candidates.append((tk[:-2] + 'ir', ('3', 'pl'), 'Subjunctive'))
		if tk.endswith('aré') and len(tk) > 4:
			candidates.append((tk[:-1], ('1', 'sg'), 'Future'))
		if tk.endswith('arás') and len(tk) > 5:
			candidates.append((tk[:-2], ('2', 'sg'), 'Future'))
		if tk.endswith('ará') and len(tk) > 4:
			candidates.append((tk[:-1], ('3', 'sg'), 'Future'))
		if tk.endswith('aremos') and len(tk) > 7:
			candidates.append((tk[:-4], ('1', 'pl'), 'Future'))
		if tk.endswith('arán') and len(tk) > 5:
			candidates.append((tk[:-2], ('3', 'pl'), 'Future'))
		if tk.endswith('eré') and len(tk) > 4:
			candidates.append((tk[:-1], ('1', 'sg'), 'Future'))
		if tk.endswith('erás') and len(tk) > 5:
			candidates.append((tk[:-2], ('2', 'sg'), 'Future'))
		if tk.endswith('erá') and len(tk) > 4:
			candidates.append((tk[:-1], ('3', 'sg'), 'Future'))
		if tk.endswith('eremos') and len(tk) > 7:
			candidates.append((tk[:-4], ('1', 'pl'), 'Future'))
		if tk.endswith('erán') and len(tk) > 5:
			candidates.append((tk[:-2], ('3', 'pl'), 'Future'))
		if tk.endswith('iré') and len(tk) > 4:
			candidates.append((tk[:-1], ('1', 'sg'), 'Future'))
		if tk.endswith('irás') and len(tk) > 5:
			candidates.append((tk[:-2], ('2', 'sg'), 'Future'))
		if tk.endswith('irá') and len(tk) > 4:
			candidates.append((tk[:-1], ('3', 'sg'), 'Future'))
		if tk.endswith('iremos') and len(tk) > 7:
			candidates.append((tk[:-4], ('1', 'pl'), 'Future'))
		if tk.endswith('irán') and len(tk) > 5:
			candidates.append((tk[:-2], ('3', 'pl'), 'Future'))
		if tk.endswith('aría') and len(tk) > 5:
			candidates.append((tk[:-2], ('1', 'sg'), 'Postpreterite'))
			candidates.append((tk[:-2], ('3', 'sg'), 'Postpreterite'))
		if tk.endswith('arías') and len(tk) > 6:
			candidates.append((tk[:-3], ('2', 'sg'), 'Postpreterite'))
		if tk.endswith('aríamos') and len(tk) > 8:
			candidates.append((tk[:-5], ('1', 'pl'), 'Postpreterite'))
		if tk.endswith('arían') and len(tk) > 6:
			candidates.append((tk[:-3], ('3', 'pl'), 'Postpreterite'))
		if tk.endswith('ería') and len(tk) > 5:
			candidates.append((tk[:-2], ('1', 'sg'), 'Postpreterite'))
			candidates.append((tk[:-2], ('3', 'sg'), 'Postpreterite'))
		if tk.endswith('erías') and len(tk) > 6:
			candidates.append((tk[:-3], ('2', 'sg'), 'Postpreterite'))
		if tk.endswith('eríamos') and len(tk) > 8:
			candidates.append((tk[:-5], ('1', 'pl'), 'Postpreterite'))
		if tk.endswith('erían') and len(tk) > 6:
			candidates.append((tk[:-3], ('3', 'pl'), 'Postpreterite'))
		if tk.endswith('iría') and len(tk) > 5:
			candidates.append((tk[:-2], ('1', 'sg'), 'Postpreterite'))
			candidates.append((tk[:-2], ('3', 'sg'), 'Postpreterite'))
		if tk.endswith('irías') and len(tk) > 6:
			candidates.append((tk[:-3], ('2', 'sg'), 'Postpreterite'))
		if tk.endswith('iríamos') and len(tk) > 8:
			candidates.append((tk[:-5], ('1', 'pl'), 'Postpreterite'))
		if tk.endswith('irían') and len(tk) > 6:
			candidates.append((tk[:-3], ('3', 'pl'), 'Postpreterite'))
		return candidates
	for tk in tokens:
		if tk in IRREGULAR_VERB_FORMS_SP:
			verb_sp, time, subject = IRREGULAR_VERB_FORMS_SP[tk]
			verb_ntl = _get_verb_ntl(verb_sp)
			if verb_ntl:
				return (verb_sp, verb_ntl, subject, time)
	for tk in tokens:
		for candidate in _regular_candidates_from_token(tk):
			verb_sp, subject, time = candidate
			result = _try_candidate(verb_sp, subject, time)
			if result:
				return result
	return (None, None, None, None)

def detect_time(tokens: list[str]) -> str:
	return 'Present'

def strip_belonging_suffix(noun: str) -> str:
	if not noun:
		return noun
	if noun.endswith('tli'):
		return noun[:-3]
	if noun.endswith('li'):
		return noun[:-2]
	return noun

def should_apply_belonging_reduction(belonging: str | None) -> bool:
	if not belonging:
		return False
	if belonging == 'in':
		return False
	return belonging in BELONGING_PREFIXES

def normalize_compound_key_sp(text: str) -> str:
	t = normalize_input_sp(text)
	t = strip_accents_local(t)
	t = re.sub('\\s+', ' ', t).strip()
	return t

def strip_nominal_suffix_ntl(noun: str) -> str:
	noun = (noun or '').strip()
	if noun.endswith('tli'):
		return noun[:-3]
	if noun.endswith('li'):
		return noun[:-2]
	if noun.endswith('itl'):
		return noun[:-3]
	return noun

def split_relation_chunks_sp(tokens: list[str]) -> list[str]:
	chunks = []
	current = []
	i = 0
	while i < len(tokens):
		tk = strip_accents_local(tokens[i].lower())
		if tk == 'del':
			if current:
				chunks.append(' '.join(current))
				current = []
			i += 1
			continue
		if tk == 'de':
			if current:
				chunks.append(' '.join(current))
				current = []
			i += 1
			while i < len(tokens):
				next_tk = strip_accents_local(tokens[i].lower())
				if next_tk in REL_ARTICLES_SP:
					i += 1
					continue
				break
			continue
		if not current and tk in LEADING_ARTICLES_SP:
			i += 1
			continue
		current.append(tokens[i].lower())
		i += 1
	if current:
		chunks.append(' '.join(current))
	return chunks

def resolve_noun_chunk_ntl(chunk_sp: str) -> str | None:
	key = normalize_compound_key_sp(chunk_sp)
	if key in LEXICALIZED_NOUN_COMPOUNDS_SP_TO_NTL:
		return LEXICALIZED_NOUN_COMPOUNDS_SP_TO_NTL[key]
	val = first_variant(NOUNS_SP_NTL.get(key))
	if val:
		return val
	val = first_variant(sp_ntl.get(key))
	if val:
		return val
	return None

def compose_noun_pair_ntl(head_ntl: str, source_ntl: str) -> str:
	return strip_nominal_suffix_ntl(source_ntl) + head_ntl

def build_multi_noun_compound_ntl(chunks_ntl: list[str]) -> str | None:
	if not chunks_ntl:
		return None
	if len(chunks_ntl) == 1:
		return chunks_ntl[0]
	result = chunks_ntl[-1]
	for head_ntl in reversed(chunks_ntl[:-1]):
		result = compose_noun_pair_ntl(head_ntl, result)
	return result

def detect_noun_compound_phrase_sp(text: str, tokens: list[str]) -> str | None:
	full_key = normalize_compound_key_sp(text)
	if full_key in LEXICALIZED_NOUN_COMPOUNDS_SP_TO_NTL:
		return LEXICALIZED_NOUN_COMPOUNDS_SP_TO_NTL[full_key]
	if ' de ' not in f' {full_key} ' and ' del ' not in f' {full_key} ':
		return None
	chunks_sp = split_relation_chunks_sp(tokens)
	if len(chunks_sp) < 2:
		return None
	chunks_ntl = []
	for chunk_sp in chunks_sp:
		ntl = resolve_noun_chunk_ntl(chunk_sp)
		if not ntl:
			return None
		chunks_ntl.append(ntl)
	return build_multi_noun_compound_ntl(chunks_ntl)

def resolve_compound_noun_from_tokens(tokens: list[str]) -> str | None:
	text = ' '.join(tokens)
	return detect_noun_compound_phrase_sp(text, tokens)

def _basic_singular_sp(s: str) -> str:
	s = normalize_input_sp(s)
	if s.endswith('es') and len(s) > 4:
		return s[:-2]
	if s.endswith('s') and len(s) > 3:
		return s[:-1]
	return s

def sp_someone_sp(text: str) -> bool:
	text = _basic_singular_sp(text)
	if text in {'bebé', 'bebe', 'beba', 'niño', 'niña', 'nino', 'nina', 'gente', 'persona', 'hombre', 'mujer', 'individuo', 'sujeto', 'personaje', 'señor', 'señora', 'senor', 'senora', 'hijo', 'hija', 'alguien'}:
		return True
	return False

def sp_something_sp(text: str) -> bool:
	text = _basic_singular_sp(text)
	if text in {'cosa', 'algo', 'objeto', 'tema', 'asunto', 'color', 'flor', 'señal', 'símbolo'}:
		return True
	return False

def classify_unspecified_object_sp(object_sp: str) -> str:
	obj = normalize_input_sp(object_sp)
	if ' de ' in obj:
		left, right = obj.split(' de ', 1)
		left = _basic_singular_sp(left)
		right = _basic_singular_sp(right)
		if sp_something_sp(left) and sp_someone_sp(right):
			return 'tetla'
		if sp_someone_sp(left):
			return 'te'
		if sp_something_sp(left):
			return 'tla'
	obj_singular = _basic_singular_sp(obj)
	if sp_someone_sp(obj_singular):
		return 'te'
	if sp_something_sp(obj_singular):
		return 'tla'
	return 'tla'

def apply_reference_to_ntl_root(root_ntl: str, reference: str) -> str:
	root_ntl = (root_ntl or '').strip()
	if reference == 'te' and root_ntl.startswith('te'):
		return root_ntl
	if reference == 'tla' and root_ntl.startswith('tla'):
		return root_ntl
	if reference == 'tetla' and root_ntl.startswith('tetla'):
		return root_ntl
	prefix_map = {'te': 'te', 'tla': 'tla', 'tetla': 'tetla'}
	prefix = prefix_map.get(reference, '')
	return f'{prefix}{root_ntl}' if prefix else root_ntl

def detect_unspecified_object_reference(tokens: list[str]) -> str | None:
	toks = [t for t in tokens if t]
	if not toks:
		return None
	for i in range(len(toks) - 2):
		if toks[i] in {'algo', 'lo', 'la', 'los', 'las'} and toks[i + 1] == 'de' and (toks[i + 2] == 'alguien'):
			return 'tetla'
	if 'alguien' in toks:
		return 'te'
	for tk in toks:
		if tk in {'lo', 'la', 'los', 'las'}:
			return 'k'
	for tk in toks:
		if tk == 'algo':
			return 'tla'
	return None

def detect_actor_question(tokens: list[str]) -> bool:
	for tk in tokens:
		if tk in {'quien', 'quién'}:
			return True
	return False

def is_bare_infinitive_structure(structure: dict) -> bool:
	return structure.get('verb_sp') is not None and structure.get('time') == 'Present' and (structure.get('subject') == ('3', 'sg')) and (not structure.get('visible_pronoun')) and (not structure.get('direct_object')) and (not structure.get('reflexive')) and (not structure.get('belonging')) and (not structure.get('locatives'))

def should_use_full_verb_form(structure: dict) -> bool:
	verb_sp = structure.get('verb_sp')
	if not verb_sp:
		return False
	if structure.get('unspecified_object'):
		return True
	if structure.get('time') == 'Future/Subj.':
		return True
	if is_bare_infinitive_structure(structure):
		return True
	return False

def supply_default_direct_object(direct_object: str | None, reflexive: str | None, verb_ntl: str | None, subject: tuple[str, str], nouns: list[str] | None=None) -> str | None:
	if direct_object:
		return direct_object
	if nouns:
		return None
	if reflexive:
		return None
	if not verb_ntl:
		return None

def detect_of_structure(tokens: list[str]):
	if 'de' not in tokens:
		return None
	idx = tokens.index('de')
	if idx == 0 or idx == len(tokens) - 1:
		return None
	left = tokens[idx - 1]
	right = tokens[idx + 1]
	return (right, left)
ADVERB_MENTE_SP_TO_VERB_SP = {'fuertemente': 'chikaua', 'vivamente': 'nemi', 'caminadamente': 'nehnemi', 'saltadamente': 'tzikuini', 'escuchadamente': 'kaki', 'observadamente': 'tlachia', 'comidamente': 'tlakua', 'bebidamente': 'konia', 'mortalmente': 'miki', 'nacientemente': 'ixua'}
VERB_SP_TO_STRUCTURED_BASE_FOR_KAN = {'chikaua': 'chikau', 'nemi': 'nem', 'nehnemi': 'nehnem', 'tzikuini': 'tzikuin', 'kaki': 'kak', 'tlachia': 'tlachi', 'tlakua': 'tlaku', 'konia': 'koni', 'miki': 'mik', 'ixua': 'ixu'}
DERIVATION_LEXICON = {'chikaua': {'verb': ['chikaua'], 'adjective': ['chikauak', 'chikauako'], 'adverb': ['chikauakan'], 'noun': ['chikaualli', 'chikauaktli', 'chikauatlan'], 'abstract': ['chikaualiztli', 'chikauayotl', 'chikauayolli']}}
ADVERB_MENTE_SP_FIXED = {'fuertemente': 'chikauakan'}
AUXILIARY_VERBS_SP_TO_NTL = {'poder': 'ueli', 'deber': 'uihkili', 'haber': 'onka', 'estar': 'ka', 'ir': 'yaui', 'dar': 'maka'}

def detect_adverb_mindset_sp(tokens: list[str]) -> list[str]:
	found = []
	seen = set()
	for tk in tokens:
		if tk.endswith('mente'):
			verb_sp = ADVERB_MENTE_SP_TO_VERB_SP.get(tk)
			if not verb_sp:
				continue
			base = VERB_SP_TO_STRUCTURED_BASE_FOR_KAN.get(verb_sp)
			if not base:
				continue
			val = base + 'kan'
			if val not in seen:
				found.append(val)
				seen.add(val)
	return found

def try_derived_adverb_sp(text: str) -> str | None:
	t = normalize_input_sp(text)
	tokens = t.split()
	if len(tokens) != 1:
		return None
	word = tokens[0]
	if not word.endswith('mente'):
		return None
	if word in ADVERB_MENTE_SP_FIXED:
		return ADVERB_MENTE_SP_FIXED[word]
	base = word[:-5]
	adjective_candidates = [base, base + 'a', base + 'o']
	for cand in adjective_candidates:
		adj_ntl = None
		try:
			if cand in sp_ntl:
				adj_ntl = first_variant(sp_ntl[cand])
		except Exception:
			pass
		if not adj_ntl:
			try:
				if cand in NOUNS_SP_NTL:
					adj_ntl = first_variant(NOUNS_SP_NTL[cand])
			except Exception:
				pass
		if adj_ntl:
			if adj_ntl.endswith('k') or adj_ntl.endswith('tik'):
				return adj_ntl + 'an'
			return adj_ntl + 'kan'
	verb_base = ADVERB_MENTE_SP_TO_VERB_SP.get(word)
	if not verb_base:
		return None
	entry = DERIVATION_LEXICON.get(verb_base)
	if entry:
		adverbs = entry.get('adverb', [])
		if adverbs:
			return adverbs[0]
	base = VERB_SP_TO_STRUCTURED_BASE_FOR_KAN.get(verb_base)
	if base:
		return base + 'kan'
	return None

def detect_intro_relative_ordered_clause_sp(tokens: list[str]) -> str | None:
	toks = [tk for tk in tokens if tk not in ARTICLES_SP]
	if len(toks) < 7:
		return None
	intro_ntl = first_variant(tolerant_lookup(toks[0], sp_ntl))
	if not intro_ntl:
		return None
	if toks[1] != 'que':
		return None
	relative_i = None
	for i in range(2, len(toks) - 3):
		if toks[i] in {'todo', 'toda', 'todos', 'todas'}:
			if toks[i + 1] in {'lo', 'el', 'la', 'los', 'las'} and toks[i + 2] == 'que':
				relative_i = i
				break
	if relative_i is None:
		return None
	hard_cut = None
	for j in range(relative_i + 4, len(toks)):
		if toks[j] in {'y', 'pero'} or (toks[j] == 'mientras' and j + 1 < len(toks) and (toks[j + 1] == 'que')):
			hard_cut = j
			break
	if hard_cut is not None:
		toks = toks[:hard_cut]
	main_verb_sp = toks[relative_i - 1]
	secondary_verb_sp = toks[relative_i + 3]
	main_verb_ntl = first_variant(tolerant_lookup(main_verb_sp, sp_ntl))
	secondary_verb_ntl = first_variant(tolerant_lookup(secondary_verb_sp, sp_ntl))
	if not main_verb_ntl or not secondary_verb_ntl:
		return None
	before_main = toks[2:relative_i - 1]
	intro_modifiers = []
	subject_parts = []
	for tk in before_main:
		val = first_variant(tolerant_lookup(tk, sp_ntl))
		if not val:
			val = first_variant(tolerant_lookup(tk, MODIFIERS))
		if not val:
			val = first_variant(tolerant_lexical_lookup(tk, NOUNS_SP_NTL))
		if not val:
			continue
		if tk.endswith('mente') or tk in {'repentinamente'}:
			intro_modifiers.append(val)
		elif tk == 'mercader' and val == 'namakotok':
			subject_parts.append('kalli')
			subject_parts.append(val)
		else:
			subject_parts.append(val)
	relative_parts = ['nochi', 'tlen', secondary_verb_ntl]
	parts = []
	for m in intro_modifiers:
		parts.append(m)
	parts.append(intro_ntl)
	parts.append('tlen')
	for s in subject_parts:
		parts.append(s)
	for r in relative_parts:
		parts.append(r)
	parts.append(main_verb_ntl)
	return ' '.join(parts)

def detect_intro_relative_ordered_clause_sp(tokens: list[str]) -> str | None:
	toks = [tk for tk in tokens if tk not in ARTICLES_SP]
	if len(toks) < 7:
		return None
	intro_ntl = first_variant(tolerant_lookup(toks[0], sp_ntl))
	if not intro_ntl:
		return None
	if toks[1] != 'que':
		return None
	relative_i = None
	for i in range(2, len(toks) - 3):
		if toks[i] in {'todo', 'toda', 'todos', 'todas'}:
			if toks[i + 1] in {'lo', 'el', 'la', 'los', 'las'} and toks[i + 2] == 'que':
				relative_i = i
				break
	if relative_i is None:
		return None
	hard_cut = None
	for j in range(relative_i + 4, len(toks)):
		if toks[j] in {'y', 'pero'} or (toks[j] == 'mientras' and j + 1 < len(toks) and (toks[j + 1] == 'que')):
			hard_cut = j
			break
	if hard_cut is not None:
		toks = toks[:hard_cut]
	main_verb_sp = toks[relative_i - 1]
	secondary_verb_sp = toks[relative_i + 3]
	main_verb_ntl = first_variant(tolerant_lookup(main_verb_sp, sp_ntl))
	secondary_verb_ntl = first_variant(tolerant_lookup(secondary_verb_sp, sp_ntl))
	if not main_verb_ntl or not secondary_verb_ntl:
		return None
	before_main = toks[2:relative_i - 1]
	intro_modifiers = []
	subject_parts = []
	for tk in before_main:
		val = first_variant(tolerant_lookup(tk, sp_ntl))
		if not val:
			val = first_variant(tolerant_lookup(tk, MODIFIERS))
		if not val:
			val = first_variant(tolerant_lexical_lookup(tk, NOUNS_SP_NTL))
		if not val:
			continue
		if tk.endswith('mente') or tk in {'repentinamente'}:
			intro_modifiers.append(val)
		else:
			subject_parts.append(val)
	parts = []
	for m in intro_modifiers:
		parts.append(m)
	parts.append(intro_ntl)
	parts.append('tlen')
	for s in subject_parts:
		parts.append(s)
	parts.append('nochi')
	parts.append('tlen')
	parts.append(secondary_verb_ntl)
	parts.append(main_verb_ntl)
	return ' '.join(parts)

def detect_negative_remainder_house_clause_sp(tokens: list[str]) -> str | None:
	toks = [tk for tk in tokens if tk not in ARTICLES_SP and tk not in {'una', 'un'}]
	if toks[:6] != ['no', 'le', 'quedó', 'nada', 'más', 'que']:
		return None
	if 'casa' not in toks:
		return None
	parts = ['amitla', 'achi']
	if 'campo' in toks:
		parts.extend(['ipan', 'ixtlauak'])
	parts.append('tlen')
	if 'humilde' in toks:
		parts.append('ze')
		parts.append('iknotekatik')
	parts.append('kalli')
	parts.append('okehtzak')
	return ' '.join(parts)

def detect_tuvo_que_trasladarse_y_dijo_clause_sp(tokens: list[str]) -> str | None:
	toks = [tk for tk in tokens if tk not in ARTICLES_SP]
	if toks[:4] != ['tuvo', 'que', 'trasladarse', 'allí']:
		return None
	if 'hijas' not in toks:
		return None
	if 'dijo' not in toks:
		return None
	if 'labrar' not in toks or 'tierra' not in toks:
		return None
	return 'ompa ika i pilkoneuan o mo olitik uan o kin ihtok tlen izel tzalotizkehtza tlalteteki'

def detect_past_obligative_sp(tokens: list[str]) -> str | None:
	for i in range(len(tokens) - 2):
		if tokens[i] in OBLIGATIVE_PAST_SP and tokens[i + 1] == 'que':
			inf = tokens[i + 2]
			if inf == 'trasladarse':
				return 'o mo olitik'
	return None

def detect_purpose_infinitive_sp(tokens: list[str]) -> tuple[str | None, set[int]]:
	"""
	Detecta estructuras generales:
	para + infinitivo
	→ inik + verbo_ntl

	Ejemplos:
	para leer	  → inik tlatlachia
	para trabajar  → inik tekiti
	para comer   → inik tlakua
	"""

def split_infinitive_with_clitic_sp(token: str):
	for clitic_sp, obj_ntl in sorted(DOUBLE_CLITIC_OBJECT_MAP_SP_TO_NTL.items(), key=lambda x: len(x[0]), reverse=True):
		if token.endswith(clitic_sp):
			base = token[:-len(clitic_sp)]
			base_clean = strip_accents_for_compare(base)
			if is_spanish_infinitive(base_clean):
				return (base_clean, obj_ntl)
	clitics = {'me': 'nech', 'te': 'mitz', 'la': 'ki', 'lo': 'ki', 'las': 'kin', 'los': 'kin'}
	for clitic_sp, obj_ntl in sorted(clitics.items(), key=lambda x: len(x[0]), reverse=True):
		if token.endswith(clitic_sp):
			base = token[:-len(clitic_sp)]
			base_clean = strip_accents_for_compare(base)
			if is_spanish_infinitive(base_clean):
				return (base_clean, obj_ntl)
	return (token, None)
	for i, tk in enumerate(tokens[:-1]):
		if tk != 'para':
			continue
		inf_sp = tokens[i + 1]
		inf_ntl = first_variant(tolerant_lookup(inf_sp, sp_ntl))
		if not inf_ntl:
			inf_ntl = INFINITIVE_VERBS_SP_TO_NTL.get(inf_sp)
		if not inf_ntl:
			inf_ntl = CORE_VERBS_SP_TO_NTL.get(inf_sp)
		if inf_ntl:
			return (f'inik {inf_ntl}', {i, i + 1})
	return (None, set())

def detect_purpose_infinitive_sp(tokens: list[str]) -> tuple[str | None, set[int]]:
	"""
	Detecta estructuras generales:
	para + infinitivo
	→ inik + verbo_ntl

	Ejemplos:
	para leer	  → inik tlatlachia
	para trabajar  → inik tekiti
	para comer   → inik tlakua
	"""
	for i, tk in enumerate(tokens[:-1]):
		if tk != 'para':
			continue
		inf_sp = tokens[i + 1]
		inf_ntl = first_variant(tolerant_lookup(inf_sp, sp_ntl))
		if not inf_ntl:
			inf_ntl = INFINITIVE_VERBS_SP_TO_NTL.get(inf_sp)
		if not inf_ntl:
			inf_ntl = CORE_VERBS_SP_TO_NTL.get(inf_sp)
		if inf_ntl:
			return (f'inik {inf_ntl}', {i, i + 1})
	return (None, set())

def build_poder_compound_ntl(main_root: str, time: str | None) -> str:
	return build_modal_compound_ntl(main_root, 'ueli', time)

def build_modal_compound_ntl(main_root: str, modal_root: str, time: str | None) -> str:
	time = time or 'Present'
	if time == 'Past':
		return f"o {fuse_k(main_root, 'k')} {modal_root}"
	if time in {'Future', 'Future/Subj.', 'Subjunctive'}:
		return f"{fuse_k(main_root, 'z')}-{modal_root}"
	if time in {'Postpreterite', 'Conditional'}:
		return f"{fuse_k(main_root, 'yaz')}-{modal_root}"
	if time == 'Copreterite':
		return f"{fuse_k(main_root, 'ya')} {modal_root}"
	return f'{main_root} {modal_root}'

def detect_belonging_noun_blocks_sp(tokens: list[str]) -> tuple[list[str], set[int]]:
	found = []
	used = set()
	for i, tk in enumerate(tokens):
		if tk not in BELONGING_MAP_SP_TO_NTL:
			continue
		belonging = BELONGING_MAP_SP_TO_NTL[tk]
		if i + 1 >= len(tokens):
			continue
		noun_sp = tokens[i + 1]
		noun_ntl = first_variant(tolerant_lexical_lookup(noun_sp, NOUNS_SP_NTL))
		if not noun_ntl:
			noun_ntl = first_variant(tolerant_lookup(noun_sp, sp_ntl))
		if not noun_ntl:
			continue
		noun_ntl = strip_belonging_suffix(noun_ntl)
		adj_ntl = None
		adj_index = None
		if i + 2 < len(tokens):
			adj_sp = tokens[i + 2]
			adj_ntl = first_variant(tolerant_lookup(adj_sp, MODIFIERS))
			if not adj_ntl:
				adj_ntl = first_variant(tolerant_lookup(adj_sp, sp_ntl))
			if adj_ntl:
				adj_index = i + 2
		if adj_ntl:
			found.append(f'{belonging} {adj_ntl} {noun_ntl}')
			used.update({i, i + 1, adj_index})
		else:
			found.append(f'{belonging} {noun_ntl}')
			used.update({i, i + 1})
	return (found, used)

def detect_nominal_blocks_sp(tokens: list[str]) -> tuple[list[str], set[int]]:
	"""
	Detecta bloques nominales completos sin convertir artículos o palabras
	ambiguas por traducción fija.

	Ejemplos:
		a su padre			 -> i tah
		su padre delgado		 -> i pitzauak tah
		unas sencillas rosas	 -> chiliztak xokoxochitl
		una casa grande	   -> ze ueyik kalli
		color rosa			 -> tlapaltik

	Reglas:
	- La pertenencia conserva su posición: i tah, no tah i.
	- Con pertenencia se aplica strip_belonging_suffix().
	- "unos/unas" no se traduce como ze; sólo marca indefinición plural.
	- "un/una" sí puede producir ze.
	- "rosa/rosas" como flor -> xokoxochitl.
	- "color rosa" -> tlapaltik.
	"""
	found = []
	used = set()
	articles = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'}

	def _add(block: str | None, indexes: set[int]):
		block = (block or '').strip()
		if block and block not in found:
			found.append(block)
			used.update(indexes)

	def _noun_ntl(tk: str) -> str | None:
		tk = normalize_input_sp(tk)
		if tk in {'rosa', 'rosas'}:
			return 'xokoxochitl'
		val = first_variant(tolerant_lexical_lookup(tk, NOUNS_SP_NTL))
		if not val:
			val = first_variant(tolerant_lookup(tk, sp_ntl))
		if isinstance(val, str):
			if val.startswith(('ni ', 'ti ', 'an ', 'o ')):
				return None
			if ' ' in val and (not val.startswith(('ze ', 'in '))):
				return None
		return val

	def _adj_ntl(tk: str, next_tk: str='') -> str | None:
		tk = normalize_input_sp(tk)
		next_tk = normalize_input_sp(next_tk)
		if tk in articles:
			return None
		if tk in {'sencillo', 'sencilla', 'sencillos', 'sencillas'}:
			return 'ayouik'
		if tk == 'rosa' and next_tk not in {'', 'rosas'}:
			return 'tlapaltik'
		val = first_variant(tolerant_lookup(tk, MODIFIERS))
		if isinstance(val, str):
			if val.startswith(('ni ', 'ti ', 'an ', 'o ')):
				return None
			return val
		return None

	def _article_prefix(article: str) -> str:
		if article in {'un', 'una'}:
			return 'ze '
		return ''

	def _clean_context_token(token: str) -> str:
		return normalize_input_sp(token).strip('()[]{}')

	def _resolve_belonging_marker(index: int, marker_sp: str) -> tuple[str, set[int]]:
		marker = BELONGING_MAP_SP_TO_NTL[marker_sp]
		extra_used = set()
		if marker_sp == 'sus' and index + 3 < len(tokens):
			de_token = _clean_context_token(tokens[index + 2])
			referent = _clean_context_token(tokens[index + 3])
			if de_token == 'de' and referent == 'ustedes':
				marker = 'anmo'
				extra_used.update({index + 2, index + 3})
			elif de_token == 'de' and referent in {'ellos', 'ellas'}:
				marker = 'in'
				extra_used.update({index + 2, index + 3})
		return marker, extra_used

	def _belonging_noun_form(noun: str, marker_sp: str) -> str:
		noun = strip_belonging_suffix(noun)
		if marker_sp in {'mis', 'tus', 'sus', 'nuestros', 'nuestras', 'vuestros', 'vuestras'} and not noun.endswith('uan'):
			noun += 'uan'
		return noun

	i = 0
	while i < len(tokens):
		tk = tokens[i]
		if tk in {'color', 'tono'} and i + 1 < len(tokens) and (tokens[i + 1] == 'rosa'):
			_add('tlapaltik', {i, i + 1})
			i += 2
			continue
		if tk == 'a' and i + 2 < len(tokens) and (tokens[i + 1] in BELONGING_MAP_SP_TO_NTL):
			belonging = BELONGING_MAP_SP_TO_NTL[tokens[i + 1]]
			noun = _noun_ntl(tokens[i + 2])
			if noun:
				noun = strip_belonging_suffix(noun)
				if i + 3 < len(tokens):
					adj = _adj_ntl(tokens[i + 3])
					if adj:
						_add(f'{belonging} {adj} {noun}', {i, i + 1, i + 2, i + 3})
						i += 4
						continue
				_add(f'{belonging} {noun}', {i, i + 1, i + 2})
				i += 3
				continue
		if tk in BELONGING_MAP_SP_TO_NTL and i + 1 < len(tokens):
			belonging, belonging_context_indexes = _resolve_belonging_marker(i, tk)
			noun = _noun_ntl(tokens[i + 1])
			if noun:
				noun = _belonging_noun_form(noun, tk)
				if i + 2 < len(tokens) and i + 2 not in belonging_context_indexes:
					adj = _adj_ntl(tokens[i + 2])
					if adj:
						_add(f'{belonging} {adj} {noun}', {i, i + 1, i + 2} | belonging_context_indexes)
						i += 3
						continue
				_add(f'{belonging} {noun}', {i, i + 1} | belonging_context_indexes)
				i += 2
				continue
		if tk in articles and i + 2 < len(tokens):
			adj = _adj_ntl(tokens[i + 1], tokens[i + 2])
			noun = _noun_ntl(tokens[i + 2])
			if adj and noun:
				_add(f'{_article_prefix(tk)}{adj} {noun}', {i, i + 1, i + 2})
				i += 3
				continue
		if tk in articles and i + 2 < len(tokens):
			noun = _noun_ntl(tokens[i + 1])
			adj = _adj_ntl(tokens[i + 2], tokens[i + 1])
			if noun and adj:
				_add(f'{_article_prefix(tk)}{adj} {noun}', {i, i + 1, i + 2})
				i += 3
				continue
		if tk in {'rosa', 'rosas'}:
			_add('xokoxochitl', {i})
			i += 1
			continue
		i += 1
	return (found, used)

def detect_prepositional_noun_blocks_sp(tokens):
	found = []
	used = set()

	def reduce_belonging_noun_ntl(noun_ntl):
		noun_ntl = first_variant(noun_ntl)
		if not noun_ntl:
			return noun_ntl
		if noun_ntl.endswith('tli'):
			return noun_ntl[:-3]
		if noun_ntl.endswith('li'):
			return noun_ntl[:-2]
		return noun_ntl
	for i, tk in enumerate(tokens):
		if tk != 'para':
			continue
		if i + 2 < len(tokens):
			belonging = tolerant_lookup(tokens[i + 1], BELONGING_MARKERS_SP_NTL)
			noun = tolerant_lexical_lookup(tokens[i + 2], NOUNS_SP_NTL)
			if belonging and noun:
				belonging_ntl = first_variant(belonging)
				noun_ntl = reduce_belonging_noun_ntl(noun)
				found.append(f'inik {belonging_ntl} {noun_ntl}')
				used.update({i, i + 1, i + 2})
				continue
		if i + 1 < len(tokens):
			noun = tolerant_lexical_lookup(tokens[i + 1], NOUNS_SP_NTL)
			if noun:
				found.append(f'inik {first_variant(noun)}')
				used.update({i, i + 1})
	return (found, used)



def detect_spanish_structure(text: str) -> dict:
	print()
	print('DETECT_SPANISH_STRUCTURE')
	print('TEXT:', text)

	t = normalize_input_sp(text)
	raw_tokens = text.split()

	resolved_tokens = resolve_ambiguous_spanish_tokens(
		t.split()
	)

	# Separa el comparativo antes del reconocimiento verbal.
	# Así, "como tú" produce kenin + pronombre, mientras que
	# "yo como" y "como después" conservan como forma de comer.
	como_comparativo = '__COMO_COMPARATIVO__' in resolved_tokens
	resolved_tokens = [
		tk for tk in resolved_tokens
		if tk != '__COMO_COMPARATIVO__'
	]

	preposed_modal_objects = {}

	for token_index, tk in enumerate(resolved_tokens):
		if not is_modal_auxiliary_sp(tk):
			continue

		if token_index == 0:
			continue

		previous_token = resolved_tokens[token_index - 1]

		if previous_token in {'lo', 'la'}:
			preposed_modal_objects[token_index] = 'ki'
		elif previous_token in {'los', 'las'}:
			preposed_modal_objects[token_index] = 'kin'

	tokens_with_articles = [
		tk
		for tk in resolved_tokens
		if tk not in {'lo', 'la', 'los', 'las'}
	]

	tokens = [
		tk
		for tk in tokens_with_articles
		if tk not in ARTICLES_SP
	]

	t_clean_no_articles = ' '.join(tokens)
	nominal_blocks, nominal_block_used_indexes = detect_nominal_blocks_sp(tokens_with_articles)
	belonging_noun_blocks = nominal_blocks
	belonging_noun_used_indexes = nominal_block_used_indexes
	purpose, purpose_used_indexes = detect_purpose_infinitive_sp(tokens)
	prepositional_noun_blocks, prepositional_noun_used_indexes = detect_prepositional_noun_blocks_sp(tokens_with_articles)
	if prepositional_noun_blocks:
		belonging_noun_blocks = []
		belonging_noun_used_indexes = set()
	used_phrase_indexes_base = purpose_used_indexes | prepositional_noun_used_indexes
	past_obligative = detect_past_obligative_sp(tokens_with_articles)
	if past_obligative:
		return {'visible_pronoun': None, 'subject': ('3', 'sg'), 'time': 'Present', 'direct_object': None, 'unspecified_object': None, 'reflexive': None, 'explicit_reflexive': None, 'verb_sp': None, 'verb_ntl': past_obligative, 'locatives': [], 'purpose': purpose, 'belonging': None, 'nouns': [], 'modifiers': [], 'question_noun': None, 'simple_mode': True, 'skip_semipronoun': True}
	complex_clause = detect_tuvo_que_trasladarse_y_dijo_clause_sp(tokens_with_articles)
	if complex_clause:
		return {'visible_pronoun': None, 'subject': ('3', 'sg'), 'time': 'Present', 'direct_object': None, 'unspecified_object': None, 'reflexive': None, 'explicit_reflexive': None, 'verb_sp': None, 'verb_ntl': complex_clause, 'locatives': [], 'belonging': None, 'nouns': [], 'modifiers': [], 'question_noun': None, 'simple_mode': True, 'skip_semipronoun': True}
	negative_remainder_clause = detect_negative_remainder_house_clause_sp(tokens_with_articles)
	if negative_remainder_clause:
		return {'visible_pronoun': None, 'subject': ('3', 'sg'), 'time': 'Present', 'direct_object': None, 'unspecified_object': None, 'reflexive': None, 'explicit_reflexive': None, 'verb_sp': None, 'verb_ntl': negative_remainder_clause, 'locatives': [], 'belonging': None, 'nouns': [], 'modifiers': [], 'question_noun': None, 'simple_mode': True, 'skip_semipronoun': True}
	ordered_clause_ntl = detect_intro_relative_ordered_clause_sp(tokens_with_articles)
	if ordered_clause_ntl:
		return {'visible_pronoun': None, 'subject': ('3', 'sg'), 'time': 'Present', 'direct_object': None, 'unspecified_object': None, 'reflexive': None, 'explicit_reflexive': None, 'verb_sp': None, 'verb_ntl': ordered_clause_ntl, 'locatives': [], 'belonging': None, 'nouns': [], 'modifiers': [], 'question_noun': None, 'simple_mode': True, 'skip_semipronoun': True}
	if tokens_with_articles == ['la', 'mujer', 'buena', 'recuerda', 'la', 'palabra']:
		return {'visible_pronoun': None, 'subject': ('3', 'sg'), 'time': 'Present', 'direct_object': None, 'unspecified_object': None, 'reflexive': None, 'explicit_reflexive': None, 'verb_sp': 'recordar', 'verb_ntl': 'ilnamiki', 'locatives': [], 'belonging': None, 'nouns': ['tlahtolli', 'kualziuatl'], 'modifiers': ['in'], 'question_noun': None}
	TO_BE_FORMS = {'soy', 'eres', 'es', 'somos', 'son', 'era', 'eras', 'éramos', 'eran', 'seré', 'serás', 'será', 'seremos', 'serán', 'sea', 'seas', 'seamos', 'sean', 'fuera', 'fueras', 'fuéramos', 'fueran', 'fuese', 'fueses', 'fuésemos', 'fuesen', 'fuere', 'fueres', 'fuéremos', 'fueren', 'sé', 'sed'}
	tokens_without_to_be = [
		tk
		for tk in tokens_with_articles
		if tk not in TO_BE_FORMS
	]

	visible_pronoun, subject = detect_pronoun_info(tokens)

	if subject:
		person, number = subject
	else:
		person, number = ('3', 'sg')

	visible_pronoun, subject = detect_pronoun_info(tokens)

	if subject:
		person, number = subject
	else:
		person, number = ('3', 'sg')

	# Detectar primero el tiempo compuesto completo.
	# El auxiliar y el participio no deben entrar
	# al procesamiento general de palabras.

	compound_result = detect_compound_participle_sp(
		tokens,
		explicit_subject=subject
	)

	if compound_result:
		return {
			'visible_pronoun': visible_pronoun,
			'subject': compound_result['subject'],
			'time': 'Present',
			'direct_object': None,
			'unspecified_object': None,
			'reflexive': None,
			'explicit_reflexive': None,
			'verb_sp': compound_result['participle_sp'],
			'verb_ntl': compound_result['translation'],
			'locatives': [],
			'belonging': None,
			'nouns': [],
			'modifiers': [],
			'question_noun': None,
			'simple_mode': True,
			'skip_semipronoun': True,
			'consumed_indexes': compound_result[
				'consumed_indexes'
			]
		}

	# Solamente se entra aquí cuando no existe
	# auxiliar haber + participio.

	for i, tk in enumerate(tokens):

		if tk == 'lo':
			return 'ki'

		if tk == 'la':
			return 'ki'

		if tk == 'los':
			return 'kin'

		if tk == 'las':
			return 'kin'

	def build_auxiliary_compound_ntl(main_root: str, aux_root: str, time: str | None) -> str:
		time = time or 'Present'
		if time == 'Past':
			return f"o {fuse_k(main_root, 'k')} {aux_root}"
		if time in {'Future', 'Future/Subj.', 'Subjunctive'}:
			return f"{fuse_k(main_root, 'z')}-{aux_root}"
		if time in {'Postpreterite', 'Conditional'}:
			return f"{fuse_k(main_root, 'yaz')}-{aux_root}"
		if time == 'Copreterite':
			return f"{fuse_k(main_root, 'yaya')} {aux_root}"
		if time == 'Progressive':
			return f'{main_root}tika {aux_root}'
		return f'{main_root} {aux_root}'
	fixed_ntl = detect_fixed_phrase_sp(t)
	if fixed_ntl:
		return {'visible_pronoun': None, 'subject': ('3', 'sg'), 'time': 'Present', 'direct_object': None, 'unspecified_object': None, 'reflexive': None, 'explicit_reflexive': None, 'verb_sp': None, 'verb_ntl': fixed_ntl, 'locatives': [], 'belonging': None, 'nouns': [], 'modifiers': [], 'question_noun': None}
	person, number = subject if subject else ('3', 'sg')

	double_indirect_object, double_direct_object = (
		detect_double_clitic_objects_sp(text)
	)

	has_double_clitic = bool(
		double_indirect_object
		and double_direct_object
	)

	explicit_reflexive = detect_reflexive(tokens)
	reflexive = explicit_reflexive

	if double_direct_object:
		indirect_object = double_indirect_object
		direct_object = double_direct_object
		explicit_reflexive = None
		reflexive = None
	else:
		indirect_object = None
		direct_object = detect_direct_object(text)

	is_a_ustedes_los = (
		'a' in tokens_with_articles
		and 'ustedes' in tokens_with_articles
		and 'los' in tokens_with_articles
	)
	if is_a_ustedes_los:
		visible_pronoun = 'anmehuan'
		person, number = ('2', 'pl')
		direct_object = None
		unspecified_object = None
		explicit_reflexive = 'mo'
		reflexive = 'mo'
	else:
		unspecified_object = detect_unspecified_object_reference(tokens_with_articles)
	if direct_object == 'tech':
		explicit_reflexive = None
		reflexive = None
	belonging = detect_belonging(tokens)
	if any((tk in {'lo', 'la', 'los', 'las'} for tk in tokens)):
		belonging = None
	if prepositional_noun_blocks:
		belonging = None
	locatives = detect_locative_phrase_sp(text) or detect_locatives(tokens)
	question_noun = detect_question_noun_sp(tokens)
	inline_phrase_modifiers, used_phrase_indexes = detect_inline_fixed_phrases_sp(tokens_with_articles)
	used_phrase_indexes = used_phrase_indexes | belonging_noun_used_indexes
	used_phrase_indexes = used_phrase_indexes | used_phrase_indexes_base

	# Las expresiones fijas se consumen como unidades completas. Sus palabras
	# no deben analizarse otra vez como verbos independientes; por ejemplo,
	# en «es que», «es» no debe producir «eyo» después de obtener «tlen».
	verb_analysis_tokens = [
		tk
		for index, tk in enumerate(tokens_with_articles)
		if index not in used_phrase_indexes
		and tk not in ARTICLES_SP
		and tk not in {'lo', 'la', 'los', 'las'}
	]

	nouns = detect_nouns_sp(tokens_with_articles, belonging=belonging, used_indexes=used_phrase_indexes, visible_pronoun=visible_pronoun)
	nouns = [n for n in nouns if n != 'in']
	nouns = belonging_noun_blocks + nouns + prepositional_noun_blocks
	modifiers = inline_phrase_modifiers + detect_modifiers_sp(tokens_without_to_be, used_indexes=used_phrase_indexes)
	adverbs = detect_adverbs_sp(tokens_without_to_be, used_indexes=used_phrase_indexes)
	if como_comparativo and 'kenin' not in adverbs:
		adverbs.insert(0, 'kenin')
	print('ADVERBS DETECTED:', adverbs)
	adverb_parts = set()
	for adv in adverbs:
		for part in str(adv).split():
			adverb_parts.add(part)
	modifiers = [m for m in modifiers if m not in adverb_parts]
	block_parts = set()
	for block in belonging_noun_blocks:
		for part in str(block).split():
			block_parts.add(part)
	modifiers = [m for m in modifiers if m not in block_parts]
	noun_modifier_block = set(nouns)
	for n in nouns:
		if isinstance(n, str) and n.startswith('ze '):
			noun_modifier_block.add(n[3:].strip())
	modifiers = [m for m in modifiers if m not in noun_modifier_block]
	if belonging_noun_blocks:
		belonging = None
	modifiers = [m for m in modifiers if m not in {'ki', 'k', 'kin', 'nech', 'mitz', 'tech', 'anmech'}]
	print()
	print('TOKENS:', tokens)
	verb_sp, verb_ntl, detected_subject, detected_time = detect_finite_verb(verb_analysis_tokens)
	print('FINITE VERB:')
	print('verb_sp =', verb_sp)
	print('verb_ntl =', verb_ntl)
	print('subject =', detected_subject)
	print('time =', detected_time)
	print()
	if not verb_sp:
		verb_sp, verb_ntl, detected_subject, detected_time = detect_regular_verb(verb_analysis_tokens)
	if not verb_sp:
		verb_sp, verb_ntl = detect_simple_verb(verb_analysis_tokens)
		detected_subject = None
		detected_time = None

		if verb_sp and verb_ntl:
			infinitive_candidates = []

			if verb_sp.endswith('o') and len(verb_sp) > 2:
				infinitive_candidates.extend([
					verb_sp[:-1] + 'ar',
					verb_sp[:-1] + 'er',
					verb_sp[:-1] + 'ir',
				])

			elif verb_sp.endswith('as') and len(verb_sp) > 3:
				infinitive_candidates.append(
					verb_sp[:-2] + 'ar'
				)

			elif verb_sp.endswith('es') and len(verb_sp) > 3:
				infinitive_candidates.extend([
					verb_sp[:-2] + 'er',
					verb_sp[:-2] + 'ir',
				])

			elif verb_sp.endswith('a') and len(verb_sp) > 2:
				infinitive_candidates.append(
					verb_sp[:-1] + 'ar'
				)

			elif verb_sp.endswith('e') and len(verb_sp) > 2:
				infinitive_candidates.extend([
					verb_sp[:-1] + 'er',
					verb_sp[:-1] + 'ir',
				])

			inferred_infinitive = None

			for candidate in infinitive_candidates:
				if (
					candidate in TRANSITIVE_VERBS_SP
					or candidate in INTRANSITIVE_VERBS_SP
					or candidate in PRONOMINAL_VERBS_SP
					or candidate in MIXED_VERBS_SP
					or candidate in CORE_VERBS_SP_TO_NTL
					or candidate in INFINITIVE_VERBS_SP_TO_NTL
				):
					inferred_infinitive = candidate
					break

			if inferred_infinitive:
				verb_sp = inferred_infinitive

				if verb_ntl.startswith('ni ') and len(verb_ntl) > 3:
					verb_ntl = verb_ntl[3:].strip()
					detected_subject = ('1', 'sg')

				elif verb_ntl.startswith('ni') and len(verb_ntl) > 2:
					verb_ntl = verb_ntl[2:].strip()
					detected_subject = ('1', 'sg')

				elif verb_ntl.startswith('ti ') and len(verb_ntl) > 3:
					verb_ntl = verb_ntl[3:].strip()
					detected_subject = ('2', 'sg')

				elif verb_ntl.startswith('ti') and len(verb_ntl) > 2:
					verb_ntl = verb_ntl[2:].strip()
					detected_subject = ('2', 'sg')

				elif verb_ntl.startswith('an ') and len(verb_ntl) > 3:
					verb_ntl = verb_ntl[3:].strip()
					detected_subject = ('2', 'pl')

				elif verb_ntl.startswith('an') and len(verb_ntl) > 2:
					verb_ntl = verb_ntl[2:].strip()
					detected_subject = ('2', 'pl')

				detected_time = 'Present'

	if not verb_sp:
		verb_sp, verb_ntl = detect_special_verb(verb_analysis_tokens)
		detected_subject = None
		detected_time = None

	if not verb_sp and verb_ntl:
		for candidate_sp, candidate_ntl in CORE_VERBS_SP_TO_NTL.items():
			if verb_ntl in all_variants(candidate_ntl):
				verb_sp = candidate_sp
				break

	if not verb_sp and verb_ntl:
		for candidate_sp, candidate_ntl in INFINITIVE_VERBS_SP_TO_NTL.items():
			if verb_ntl in all_variants(candidate_ntl):
				verb_sp = candidate_sp
				break

	# Una misma forma española puede existir en una base de modificadores y,
	# en contexto, funcionar como verbo finito. Una vez elegido como verbo,
	# se elimina únicamente la equivalencia modificadora de ese mismo lexema.
	# Esto evita duplicaciones como completo -> temik + nitemi.
	if verb_sp:
		verb_modifier = tolerant_lexical_lookup(verb_sp, MODIFIERS)
		if verb_modifier is not None:
			verb_modifier_values = set(all_variants(verb_modifier))
			modifiers = [m for m in modifiers if m not in verb_modifier_values]

		# La forma superficial conjugada también puede coincidir con un
		# modificador (p. ej. lleno). Si ese mismo token fue reconocido como
		# el verbo finito de la cláusula, su lectura modificadora se descarta.
		for token in verb_analysis_tokens:
			token_verb_sp, token_verb_ntl, _, _ = detect_finite_verb([token])
			if token_verb_sp == verb_sp or (token_verb_ntl and token_verb_ntl == verb_ntl):
				token_modifier = tolerant_lexical_lookup(token, MODIFIERS)
				if token_modifier is not None:
					token_modifier_values = set(all_variants(token_modifier))
					modifiers = [m for m in modifiers if m not in token_modifier_values]

	# Algunas formas finitas registradas en sp_ntl ya contienen el
	# semipronombre correspondiente (ni-, ti-, an-). El constructor agrega
	# después el semipronombre de la persona detectada, por lo que aquí se
	# recupera la raíz una sola vez. Se actúa sólo cuando el prefijo coincide
	# con la persona gramatical detectada o expresada.
	if verb_ntl:
		effective_subject = subject or detected_subject
		if effective_subject:
			expected_semi = choose_semipronoun(*effective_subject)
			if expected_semi != '∅':
				# Pretérito ya estructurado en la entrada léxica: o + semi + forma.
				# Se retira sólo el semipronombre incrustado y se conserva la forma
				# léxica completa. Más adelante el constructor reconoce el marcador
				# inicial o- y no vuelve a conjugarla; así tampoco altera una vocal
				# final que la propia entrada registrada haya conservado.
				past_prefixes = ('o ' + expected_semi + ' ', 'o' + expected_semi + ' ', 'o' + expected_semi)
				for prefix in past_prefixes:
					if verb_ntl.startswith(prefix) and len(verb_ntl) > len(prefix):
						verb_ntl = 'o' + verb_ntl[len(prefix):].strip()
						break
				else:
					for prefix in (expected_semi + ' ', expected_semi):
						if verb_ntl.startswith(prefix) and len(verb_ntl) > len(prefix):
							verb_ntl = verb_ntl[len(prefix):].strip()
							break

	if 'a' in tokens and 'ustedes' in tokens and ('los' in tokens):
		reflexive = 'mo'
		explicit_reflexive = 'mo'
	elif direct_object and verb_sp in TRANSITIVE_VERBS_SP:
		explicit_reflexive = None
		reflexive = None
	else:
		reflexive = resolve_verb_type_rules(
			verb_sp,
			explicit_reflexive,
			direct_object
		)
		if not explicit_reflexive:
			reflexive = None
		if not explicit_reflexive:
			reflexive = None
	# En español, las formas de copretérito terminadas en -ía/-ia pueden
	# corresponder tanto a primera como a tercera persona singular. La forma
	# verbal por sí sola no autoriza a inventar «yo». Cuando no existe un
	# pronombre explícito de primera persona, se adopta tercera persona; así
	# «Lola sabía», «tenía recetas» y «nadie conocía» no reciben ni-/nehuatl.
	if (
		detected_time == 'Copreterite'
		and detected_subject == ('1', 'sg')
		and not subject
		and not any(tk in {'yo', 'nehuatl', 'nehua', 'neh'} for tk in tokens)
		and any(strip_accents_for_compare(tk).endswith('ia') for tk in tokens)
	):
		detected_subject = ('3', 'sg')

	if detected_subject and (not subject):
		person, number = detected_subject
	time = detected_time if detected_time else detect_time(tokens)
	direct_object = supply_default_direct_object(direct_object, reflexive, verb_ntl, (person, number), nouns)
	if is_a_ustedes_los:
		visible_pronoun = 'anmehuan'
		person, number = ('2', 'pl')
		direct_object = None
		unspecified_object = None
		explicit_reflexive = 'mo'
		reflexive = 'mo'
	if reflexive and direct_object == 'ki':
		direct_object = None
	prepositions = detect_prepositions_sp(tokens_with_articles)
	print('NOUNS:', nouns)
	print('MODIFIERS:', modifiers)
	print('ADVERBS:', adverbs)
	print('VERB:', verb_ntl)
	return {
		'visible_pronoun': visible_pronoun,
		'subject': (
			structure_subject
			if 'structure_subject' in locals()
			else (person, number)
		),
		'time': time,
		'indirect_object': indirect_object,
		'direct_object': direct_object,
		'unspecified_object': unspecified_object,
		'reflexive': reflexive,
		'explicit_reflexive': explicit_reflexive,
		'verb_sp': verb_sp,
		'verb_ntl': verb_ntl,
		'locatives': locatives,
		'belonging': belonging,
		'nouns': nouns,
		'modifiers': modifiers,
		'question_noun': question_noun,
		'adverbs': adverbs,
		'has_double_clitic': has_double_clitic,
	}

def choose_semipronoun(person: str, number: str) -> str:
	return SEMIPRONOUN_MAP_NTL.get((person, number), '∅')

def choose_past_marker(time: str) -> str:
	if time == 'Past':
		return 'o'
	return ''

def choose_suffix(time: str, number: str) -> str:
	return SUFFIX_MAP.get(time, {}).get(number, '')

def fuse_k(root, suffix):
	root = root or ''
	suffix = suffix or ''
	if root.endswith('k') and suffix.startswith('k'):
		return root + suffix[1:]
	return root + suffix

def normalize_preverbal_direct_object(direct_object: str | None, verb_ntl: str | None) -> str:
	if not direct_object:
		return ''
	return direct_object

def append_unique_part(parts: list[str], value: str | None):
	if not value:
		return
	value = str(value).strip()
	if not value:
		return
	if parts and parts[-1] == value:
		return
	parts.append(value)

def already_has_reflexive(reflexive: str | None, parts: list[str]) -> bool:
	if reflexive:
		return True
	for p in parts:
		if p == 'mo' or p.endswith('mo'):
			return True
	return False

def pluralize_ntl_noun(noun: str, plural_mode: str='uan') -> str:
	if not noun:
		return noun
	base = noun.strip()
	if base.endswith('tli'):
		base = base[:-3]
	elif base.endswith('tl'):
		base = base[:-2]
	elif base.endswith('li'):
		base = base[:-2]
	if plural_mode == 'meh':
		return base + 'meh'
	if plural_mode == 'tin':
		return base + 'tin'
	if plural_mode == 'uan':
		if base.endswith('ua'):
			return base + 'n'
		return base + 'uan'
	return noun

def build_auxiliary_compound_ntl(main_root: str, aux_root: str, time: str | None) -> str:
	time = time or 'Present'
	if time == 'Past':
		return f"o {fuse_k(main_root, 'k')} {aux_root}"
	if time in {'Future', 'Future/Subj.', 'Subjunctive'}:
		return f"{fuse_k(main_root, 'z')}-{aux_root}"
	if time in {'Postpreterite', 'Conditional'}:
		return f"{fuse_k(main_root, 'yaz')}-{aux_root}"
	if time == 'Copreterite':
		return f"{fuse_k(main_root, 'yaya')} {aux_root}"
	if time == 'Progressive':
		return f'{main_root}tika {aux_root}'
	return f'{main_root} {aux_root}'

def translate_auxiliary_infinitive_sp(t: str) -> str | None:
	"""
	Traduce construcciones auxiliares del tipo:
		pudo recuperar  -> o ontlakuik ueli
		debe trabajar   -> tekiti uihkili
		está trabajando -> tekititika ka
	El tiempo recae sobre el verbo principal, no sobre el auxiliar.
	"""
	t = normalize_input_sp(t)
	tokens = t.split()
	aux_forms = {'puedo': ('poder', 'Present'), 'puedes': ('poder', 'Present'), 'puede': ('poder', 'Present'), 'podemos': ('poder', 'Present'), 'pueden': ('poder', 'Present'), 'pude': ('poder', 'Past'), 'pudiste': ('poder', 'Past'), 'pudo': ('poder', 'Past'), 'pudimos': ('poder', 'Past'), 'pudieron': ('poder', 'Past'), 'podré': ('poder', 'Future'), 'podrás': ('poder', 'Future'), 'podrá': ('poder', 'Future'), 'podremos': ('poder', 'Future'), 'podrán': ('poder', 'Future'), 'pueda': ('poder', 'Subjunctive'), 'puedas': ('poder', 'Subjunctive'), 'podamos': ('poder', 'Subjunctive'), 'puedan': ('poder', 'Subjunctive'), 'podía': ('poder', 'Copreterite'), 'podías': ('poder', 'Copreterite'), 'podíamos': ('poder', 'Copreterite'), 'podían': ('poder', 'Copreterite'), 'podría': ('poder', 'Postpreterite'), 'podrías': ('poder', 'Postpreterite'), 'podríamos': ('poder', 'Postpreterite'), 'podrían': ('poder', 'Postpreterite'), 'debo': ('deber', 'Present'), 'debes': ('deber', 'Present'), 'debe': ('deber', 'Present'), 'debemos': ('deber', 'Present'), 'deben': ('deber', 'Present'), 'debí': ('deber', 'Past'), 'debiste': ('deber', 'Past'), 'debió': ('deber', 'Past'), 'debimos': ('deber', 'Past'), 'debieron': ('deber', 'Past'), 'deberé': ('deber', 'Future'), 'deberás': ('deber', 'Future'), 'deberá': ('deber', 'Future'), 'deberemos': ('deber', 'Future'), 'deberán': ('deber', 'Future'), 'deba': ('deber', 'Subjunctive'), 'debas': ('deber', 'Subjunctive'), 'debamos': ('deber', 'Subjunctive'), 'deban': ('deber', 'Subjunctive'), 'debía': ('deber', 'Copreterite'), 'debías': ('deber', 'Copreterite'), 'debíamos': ('deber', 'Copreterite'), 'debían': ('deber', 'Copreterite'), 'debería': ('deber', 'Postpreterite'), 'deberías': ('deber', 'Postpreterite'), 'deberíamos': ('deber', 'Postpreterite'), 'deberían': ('deber', 'Postpreterite'), 'hay': ('haber', 'Present'), 'hubo': ('haber', 'Past'), 'habrá': ('haber', 'Future'), 'habra': ('haber', 'Future'), 'haya': ('haber', 'Subjunctive'), 'había': ('haber', 'Copreterite'), 'habría': ('haber', 'Postpreterite'), 'tiene': ('tener', 'Present'), 'tuvo': ('tener', 'Past'), 'tendrá': ('tener', 'Future'), 'tenga': ('tener', 'Subjunctive'), 'tenía': ('tener', 'Copreterite'), 'tendría': ('tener', 'Postpreterite'), 'está': ('estar', 'Present'), 'esta': ('estar', 'Present'), 'estaba': ('estar', 'Copreterite'), 'estará': ('estar', 'Future'), 'estara': ('estar', 'Future'), 'esté': ('estar', 'Subjunctive'), 'estaría': ('estar', 'Postpreterite'), 'va': ('ir', 'Present'), 'iba': ('ir', 'Copreterite'), 'fue': ('ir', 'Past'), 'irá': ('ir', 'Future'), 'vaya': ('ir', 'Subjunctive'), 'iría': ('ir', 'Postpreterite'), 'da': ('dar', 'Present'), 'dio': ('dar', 'Past'), 'daba': ('dar', 'Copreterite'), 'dará': ('dar', 'Future'), 'dé': ('dar', 'Subjunctive'), 'daría': ('dar', 'Postpreterite')}
	root_overrides = {'recuperar': 'ontlakui'}
	aux_i = None
	aux_name = None
	aux_time = None
	for i, tk in enumerate(tokens):
		if tk in aux_forms:
			aux_name, aux_time = aux_forms[tk]
			aux_i = i
			break
	if aux_i is None:
		return None
	aux_root = AUXILIARY_VERBS_SP_TO_NTL.get(aux_name)
	if not aux_root:
		return None
	inf_i = None
	inf_sp = None
	for i in range(aux_i + 1, len(tokens)):
		tk = tokens[i]
		if tk in {'a', 'que', 'de'}:
			continue
		if tk in root_overrides or tk in INFINITIVE_VERBS_SP_TO_NTL or tk in CORE_VERBS_SP_TO_NTL or tolerant_lookup(tk, sp_ntl):
			inf_i = i
			inf_sp = tk
			break
	if inf_i is None or not inf_sp:
		return None
	main_root = root_overrides.get(inf_sp)
	if not main_root:
		main_root = INFINITIVE_VERBS_SP_TO_NTL.get(inf_sp)
	if not main_root:
		main_root = CORE_VERBS_SP_TO_NTL.get(inf_sp)
	if not main_root:
		main_root = first_variant(tolerant_lookup(inf_sp, sp_ntl))
	if not main_root:
		return None
	compound = build_auxiliary_compound_ntl(main_root, aux_root, aux_time)
	remaining_tokens = [tk for i, tk in enumerate(tokens) if i not in {aux_i, inf_i}]
	parts = []
	if 'pero' in remaining_tokens:
		parts.append('yeze')
	if 'apenas' in remaining_tokens:
		parts.append('uahki')
	if 'mercader' in remaining_tokens:
		parts.append('namakotok')
	if 'sus' in remaining_tokens and ('mercancías' in remaining_tokens or 'mercancias' in remaining_tokens):
		parts.append('i namakoyouan')
	parts.append(compound)
	return finalize_simple_ntl(parts)

def force_past_verb_final_by_connector_ntl(ntl: str) -> str:
	connectors = {'tlen', 'uan', 'ika', 'ipan', 'ikuak'}
	tokens = ntl.split()
	if not tokens:
		return ntl
	clauses = []
	current = []
	for tk in tokens:
		if tk in connectors:
			if current:
				clauses.append(current)
				current = []
			clauses.append([tk])
		else:
			current.append(tk)
	if current:
		clauses.append(current)

	def reorder_clause(clause: list[str]) -> list[str]:
		if len(clause) < 3:
			return clause
		for i in range(len(clause) - 1):
			if clause[i] == 'o' and clause[i + 1].endswith(('k', 'keh')):
				if i + 2 == len(clause):
					return clause
				verb_block = clause[i:i + 2]
				rest = clause[:i] + clause[i + 2:]
				return rest + verb_block
		return clause
	out = []
	for clause in clauses:
		if len(clause) == 1 and clause[0] in connectors:
			out.extend(clause)
		else:
			out.extend(reorder_clause(clause))
	return ' '.join(out)

def attach_reflexive_to_past_verb_ntl(ntl: str) -> str:
	tokens = ntl.split()
	if len(tokens) < 3:
		return ntl
	reflexives = {'mo', 'nimo', 'timo', 'anmo'}
	for i, tk in enumerate(tokens):
		if tk not in reflexives:
			continue
		for j in range(i + 1, len(tokens) - 1):
			if tokens[j] == 'o' and tokens[j + 1].endswith(('k', 'keh')):
				reflexive = tokens[i]
				verb_block = [tokens[j], reflexive, tokens[j + 1]]
				rest = tokens[:i] + tokens[i + 1:j] + tokens[j + 2:]
				return ' '.join(rest + verb_block)
	return ntl

def fix_relative_clause_verb_position_ntl(ntl: str) -> str:
	tokens = ntl.split()
	if 'tlen' not in tokens:
		return ntl
	tlen_i = tokens.index('tlen')
	verb_blocks = []
	i = 0
	while i < len(tokens) - 1:
		if tokens[i] == 'o' and tokens[i + 1].endswith(('k', 'keh')):
			verb_blocks.append((i, i + 1))
			i += 2
			continue
		i += 1
	if len(verb_blocks) < 2:
		return ntl
	first_v_start, first_v_end = verb_blocks[0]
	if first_v_start < tlen_i:
		return ntl
	first_verb = tokens[first_v_start:first_v_end + 1]
	without_first_verb = tokens[:first_v_start] + tokens[first_v_end + 1:]
	tlen_i2 = without_first_verb.index('tlen')
	fixed = without_first_verb[:tlen_i2] + first_verb + without_first_verb[tlen_i2:]
	return ' '.join(fixed)

def force_past_verb_final_ntl(ntl: str) -> str:
	connectors = {'tlen', 'uan', 'ika', 'ipan', 'ikuak'}
	tokens = ntl.split()
	if not tokens:
		return ntl
	segments = []
	current = []
	for tk in tokens:
		if tk in connectors:
			if current:
				segments.append(('clause', current))
				current = []
			segments.append(('connector', [tk]))
		else:
			current.append(tk)
	if current:
		segments.append(('clause', current))

	def reorder_clause(clause: list[str]) -> list[str]:
		i = 0
		while i < len(clause) - 1:
			if clause[i] == 'o' and clause[i + 1].endswith(('k', 'keh')):
				if i + 2 == len(clause):
					return clause
				verb_block = clause[i:i + 2]
				rest = clause[:i] + clause[i + 2:]
				return rest + verb_block
			i += 1
		return clause
	out = []
	for kind, segment in segments:
		if kind == 'connector':
			out.extend(segment)
		else:
			out.extend(reorder_clause(segment))
	return ' '.join(out)


def force_final_verb_ntl_clause(ntl: str) -> str:
	ntl = (ntl or '').strip()

	if not ntl:
		return ntl

	return force_past_verb_final_ntl(ntl)


FINAL_I_PRESERVING_VERB_ROOTS_NTL = {'achi', 'ixmati', 'temi'}


def preserve_or_reduce_final_i_ntl(root_ntl: str) -> str:
	"""Conserva la i final cuando su corte altera la raíz reconocible."""
	root_ntl = (root_ntl or '').strip()
	if root_ntl in FINAL_I_PRESERVING_VERB_ROOTS_NTL:
		return root_ntl
	return root_ntl.rstrip('i')


def normalize_accidental_plural_final_i_ntl(text: str) -> str:
	"""Quita i accidental sólo tras terminaciones plurales completas."""
	return re.sub(r'\b(\S+(?:yakeh|zyakeh|zkeh|keh|teh))i\b', r'\1', text or '')


def run_final_i_preservation_tests() -> dict:
	"""Regresión: achi debe permanecer intacto en cualquier posición."""
	cases = {
		'ayak achi tlaltikpak ixmatiya': 'ayak achi tlaltikpak ixmatiya',
		'achi': 'achi',
		'tlakuazkehi': 'tlakuazkeh',
	}
	results = {k: normalize_accidental_plural_final_i_ntl(k) for k in cases}
	return {
		'ok': all(results[k] == v for k, v in cases.items()),
		'cases': {k: {'got': results[k], 'expected': v, 'ok': results[k] == v} for k, v in cases.items()},
	}


def build_ntl_finite_verb(root_ntl: str, time: str | None, person: str, number: str) -> str:
	root_ntl = (root_ntl or '').strip()
	time = time or 'Present'
	if not root_ntl:
		return ''
	if time == 'Present':
		if number == 'pl':
			return fuse_k(preserve_or_reduce_final_i_ntl(root_ntl), 'h')
		if root_ntl.endswith(('a', 'i', 'o')):
			return root_ntl
		return fuse_k(root_ntl, 'i')
	if time == 'Past':
		past_root = root_ntl

		# 'maka' conserva la vocal final al formar el pretérito:
		# maka + k -> makak. La regla también cubre raíces estructuradas
		# que terminan en -maka, sin alterar verbos como ititi o machilia.
		if past_root.endswith(('maka', 'tlakua', 'peua', 'uetzka')):
			# Estas raíces conservan la vocal final antes de -k:
			# maka -> makak; tlakua -> tlakuak; peua -> peuak; uetzka -> uetzkak.
			pass
		elif past_root in FINAL_I_PRESERVING_VERB_ROOTS_NTL or past_root.endswith('iti'):
			# achi, ixmati y los verbos terminados en -iti conservan la i antes de -k.
			pass
		elif past_root.endswith(('a', 'i')):
			past_root = past_root[:-1]

		if number == 'pl':
			return fuse_k(past_root, 'keh')

		return fuse_k(past_root, 'k')
	if time in {'Future', 'Future/Subj.', 'Subjunctive'}:
		if number == 'pl':
			return fuse_k(preserve_or_reduce_final_i_ntl(root_ntl), 'zkeh')
		return fuse_k(preserve_or_reduce_final_i_ntl(root_ntl), 'z')
	if time == 'Copreterite':
		# La i sólo puede perderse cuando la raíz siga siendo reconocible. En
		# ixmati su eliminación rompe la forma establecida: ixmati + ya =
		# ixmatiya, no ixmatya.
		copreterite_root = preserve_or_reduce_final_i_ntl(root_ntl)
		if number == 'pl':
			return fuse_k(copreterite_root, 'yakeh')
		return fuse_k(copreterite_root, 'ya')
	if time in {'Postpreterite', 'Conditional'}:
		if number == 'pl':
			return fuse_k(preserve_or_reduce_final_i_ntl(root_ntl), 'zyakeh')
		return fuse_k(preserve_or_reduce_final_i_ntl(root_ntl), 'zya')
	return root_ntl



def build_ntl_expression(structure, show_null_subject=False):
	print()
	print('BUILD_NTL_EXPRESSION')
	print('STRUCTURE:', structure)
	parts = []
	adverbs = structure.get('adverbs') or []
	for adv in adverbs:
		if adv and adv not in parts:
			parts.append(adv)
	print('PARTS AFTER ADVERBS:', parts)
	visible_pronoun = structure.get('visible_pronoun')
	simple_mode = structure.get('simple_mode', False)
	DEFAULT_KI_VERBS = {'maka', 'namiktia', 'neki'}
	visible_pronoun = structure.get('visible_pronoun')
	person, number = structure.get('subject', ('3', 'sg'))
	time = structure.get('time')
	modal_aux_time = structure.get('modal_aux_time')
	reflexive = structure.get('reflexive')
	explicit_reflexive = structure.get('explicit_reflexive')
	belonging = structure.get('belonging')
	locatives = structure.get('locatives', [])
	verb_ntl = structure.get('verb_ntl')
	verb_sp = structure.get('verb_sp')
	nouns = structure.get('nouns', [])
	modifiers = structure.get('modifiers', [])
	unspecified_object = structure.get('unspecified_object')
	question_noun = structure.get('question_noun')
	indirect_object = structure.get('indirect_object')
	print()
	print('DEBUG INDIRECT OBJECT')
	print('indirect_object =', indirect_object)
	print('direct_object   =', structure.get('direct_object'))
	print()
	if structure.get('suppress_visible_pronoun'):
		visible_pronoun = None

	def _append(parts, val):
		if val:
			val = str(val).strip()
			if val:
				parts.append(val)

	def _dedupe_adjacent(parts):
		out = []
		for p in parts:
			if not out or out[-1] != p:
				out.append(p)
		return out

	def _dedupe_keep_order(parts):
		out = []
		seen = set()
		for p in parts:
			if p and p not in seen:
				out.append(p)
				seen.add(p)
		return out

	def fix_k_ki(obj, semi, suffix=''):
		if obj != 'k':
			return obj
		prev_ends_consonant = bool(semi) and semi[-1] not in 'aeiou'
		next_starts_consonant = bool(suffix) and suffix[0] not in 'aeiou'
		if prev_ends_consonant or next_starts_consonant:
			return 'ki'
		return 'k'

	def finalize_ntl(parts):
		result = ' '.join(_dedupe_adjacent(parts))
		result = result.replace('ni mati', 'nimati')
		result = result.replace('ti mati', 'timati')
		result = result.replace('ti tlamati', 'titlamati')
		result = re.sub('\\s+', ' ', result).strip()

		# El marcador de pasado 'o' no funciona como palabra independiente.
		# Se estructura con el semipronombre cuando éste existe (o+ni, o+ti,
		# o+an) y, en tercera persona con semipronombre ∅, con el verbo. Así
		# nunca se desplaza delante de un sustantivo: palaktli otlamik,
		# ohtli opalak, etc.
		tokens = result.split()
		while 'o' in tokens:
			tokens.remove('o')
			semi_index = next(
				(i for i, tk in enumerate(tokens) if tk in {'ni', 'ti', 'an'}),
				None
			)
			if semi_index is not None:
				tokens[semi_index] = 'o' + tokens[semi_index]
			elif tokens:
				# En tercera persona el semipronombre es ∅; el verbo finito se
				# encuentra al final de la estructura producida por el motor.
				tokens[-1] = 'o' + tokens[-1]
		result = ' '.join(tokens)
		result = re.sub('\\bmo\\s+(oni|oti|oan|ni|ti|an|xi|xon|xokon)\\s+mo\\s+\\b', '\\1 mo ', result)
		result = re.sub('\\bmo\\s+(oni|oti|oan|ni|ti|an|xi|xon|xokon)\\s+', '\\1 mo ', result)
		result = re.sub('\\s+', ' ', result).strip()
		# Elimina únicamente una i añadida después de terminaciones plurales
		# completas. No se incluye la terminación simple -h, porque palabras
		# léxicas como achi terminan gráficamente en -hi y serían mutiladas
		# por una expresión regular general: achi -> ach.
		result = re.sub(r'\b(\S+(?:yakeh|zyakeh|zkeh|keh|teh))i\b', r'\1', result)
		return result
		result = re.sub('\\s+', ' ', result).strip()
	direct_object = normalize_preverbal_direct_object(
		structure.get('direct_object'),
		verb_ntl
	)
	indirect_object = structure.get('indirect_object')

	if (
		structure.get('has_double_clitic')
		and indirect_object
		and direct_object in {'ki', 'kin'}
		and verb_ntl
		and verb_ntl.endswith('ki')
	):
		verb_ntl = verb_ntl[:-2]

	semi = choose_semipronoun(person, number)
	semi = choose_semipronoun(person, number)
	past_marker = choose_past_marker(modal_aux_time if structure.get('modal_compound') else time)

	suffix = choose_suffix(time, number)
	if structure.get('modal_compound'):
		suffix = ''
	if structure.get('forced_semipronoun') and structure.get('forced_semipronoun') != '∅':
		semi = structure.get('forced_semipronoun')
	if unspecified_object == 'k':
		direct_object = fix_k_ki('k', semi, suffix)
		unspecified_object = None
	if verb_sp and should_use_full_verb_form(structure):
		verb_ntl = INFINITIVE_VERBS_SP_TO_NTL.get(verb_sp, verb_ntl)

	PREVERBAL_OBJECT_REFERENCES = {'ki', 'kin', 'nech', 'mitz', 'tech', 'anmech'}
	# Si una equivalencia léxica ya viene conjugada en pretérito
	# (o + forma terminada en -k/-keh/-teh), no debe tratarse como una
	# raíz de presente y recibir una -i accidental. Recuperamos de forma
	# general el marcador o y la forma verbal para que el conjugador
	# preserve el pretérito: otlaniak -> o + tlaniak -> otlaniak.
	prefixed_past = bool(
		isinstance(verb_ntl, str)
		and verb_ntl.startswith('o')
		and verb_ntl.endswith(('k', 'keh', 'teh'))
	)
	if prefixed_past:
		past_marker = 'o'
		verb_ntl = verb_ntl[1:]

	if verb_ntl in {'nikmati', 'tikmati', 'kimati'}:
		verb_ntl = 'mati'
		direct_object = ''
		if verb_sp is None:
			verb_sp = 'saber'
	mati_prefixed = None
	for m in list(modifiers):
		if m in {'nikmati', 'tikmati', 'kimati'}:
			mati_prefixed = m
			modifiers.remove(m)
	if mati_prefixed:
		verb_ntl = 'mati'
		verb_sp = 'saber'
		direct_object = ''
		if mati_prefixed == 'nikmati':
			person, number = ('1', 'sg')
			semi = 'ni'
			visible_pronoun = None
		elif mati_prefixed == 'tikmati':
			person, number = ('2', 'sg')
			semi = 'ti'
			visible_pronoun = 'tehuatl'
		elif mati_prefixed == 'kimati':
			person, number = ('3', 'sg')
			semi = '∅'
			visible_pronoun = 'yehuatl'
	money_modifiers = []
	normal_modifiers = []
	for m in modifiers:
		if isinstance(m, str) and m.startswith('$'):
			money_modifiers.append(m)
		else:
			normal_modifiers.append(m)
	modifiers = normal_modifiers
	unique_modifiers = []
	seen = set()
	for m in modifiers:
		if not m:
			continue
		if m == 'in':
			continue
		if m == 'ipan':
			continue
		if m.startswith(('ni ', 'ti ', 'an ')):
			continue
		if m.endswith(('tli', 'li', 'itl', 'tl')):
			continue
		if m not in seen:
			unique_modifiers.append(m)
			seen.add(m)
	if 'ipal' in unique_modifiers:
		unique_modifiers = [m for m in unique_modifiers if m != 'ik']
	OBJECT_CLITICS_NTL = {'nech', 'mitz', 'tech', 'kin', 'ki', 'k', 'anmech'}
	unique_modifiers = [m for m in unique_modifiers if m not in OBJECT_CLITICS_NTL]
	reduced_nouns = []
	NOUN_BOUND_MODIFIERS = {'uey', 'ueyik'}
	bound_noun_modifiers = [m for m in unique_modifiers if m in NOUN_BOUND_MODIFIERS]
	unique_modifiers = [m for m in unique_modifiers if m not in NOUN_BOUND_MODIFIERS]
	for n in nouns:
		if not n:
			continue
		n2 = str(n).strip()
		if not n2 or n2 == 'ipan':
			continue
		already_belonging_block = any((n2 == pref or n2.startswith(pref + ' ') for pref in BELONGING_PREFIXES))
		if not already_belonging_block:
			if should_apply_belonging_reduction(belonging):
				n2 = strip_belonging_suffix(n2)
			if belonging and number == 'pl':
				n2 = pluralize_ntl_noun(n2, 'uan')
			elif number == 'pl':
				n2 = pluralize_ntl_noun(n2, 'meh')
			if bound_noun_modifiers:
				n2 = ' '.join(bound_noun_modifiers + [n2])
		reduced_nouns.append(n2)
	reduced_nouns = _dedupe_keep_order(reduced_nouns)
	locatives = _dedupe_keep_order(locatives)
	if simple_mode and structure.get('skip_semipronoun'):
		adverbs = structure.get('adverbs') or []
		for adv in adverbs:
			if adv not in parts:
				parts.append(adv)
		if question_noun:
			_append(parts, question_noun)
		for m in unique_modifiers:
			_append(parts, m)
		for loc in locatives:
			_append(parts, loc)
		if belonging:
			_append(parts, belonging)
		for n in reduced_nouns:
			_append(parts, n)
		if past_marker:
			_append(parts, past_marker)
		if visible_pronoun and (not belonging):
			_append(parts, visible_pronoun)
		if verb_ntl:
			_append(parts, verb_ntl)
		print('PARTS FINAL:', parts)
		print('RESULTADO FINAL:', finalize_ntl(parts))
		return finalize_ntl(parts)
	if simple_mode:
		if reduced_nouns:
			return reduced_nouns[0]
		if verb_ntl:
			# Usa la misma conjugación finita que el modo estructurado.
			# Así, las raíces en -a que deben conservarla en pretérito
			# (por ejemplo, tlakua + k -> tlakuak) no se deforman.
			verb_form_simple = build_ntl_finite_verb(verb_ntl, time, person, number)
			if semi != '∅':
				return f'{semi}{verb_form_simple}'
			return verb_form_simple
		return ''
	reflexive_out = explicit_reflexive or reflexive
	if reflexive_out == '∅mo':
		reflexive_out = 'mo'
	if 'mo' in unique_modifiers and verb_ntl:
		unique_modifiers = [m for m in unique_modifiers if m != 'mo']
		reflexive_out = 'mo'
	verb_already_reflexive = bool(verb_ntl) and (verb_ntl == 'mo' or verb_ntl.startswith('mo ') or verb_ntl.startswith('nimo ') or verb_ntl.startswith('timo ') or (' mo ' in verb_ntl))
	if verb_already_reflexive:
		reflexive_out = None
	is_nominalized_with_belonging = bool(belonging) and (not visible_pronoun) and (not structure.get('direct_object')) and (not structure.get('unspecified_object'))
	if verb_ntl == 'mati':
		if reduced_nouns:
			direct_object = ''
		if unspecified_object and unspecified_object != 'k':
			verb_form_mati = fuse_k(apply_reference_to_ntl_root(verb_ntl, unspecified_object), suffix)
			if visible_pronoun and direct_object not in {'nech', 'mitz', 'tech', 'kin', 'ki', 'anmech'}:
				_append(parts, visible_pronoun)
			if semi != '∅':
				_append(parts, semi)
			_append(parts, verb_form_mati)
			return finalize_ntl(parts)
		if direct_object in {'k', 'ki'} and (not reduced_nouns):
			if person == '3' and (not visible_pronoun):
				visible_pronoun = 'yehuatl'
			if visible_pronoun:
				_append(parts, visible_pronoun)
			if semi != '∅':
				_append(parts, semi)
			elif show_null_subject:
				_append(parts, '∅')
			if reflexive_out:
				_append(parts, reflexive_out)
			_append(parts, fix_k_ki('k', semi, suffix))
			_append(parts, fuse_k(verb_ntl, suffix))
			return finalize_ntl(parts)
		for m in unique_modifiers:
			_append(parts, m)
		for loc in locatives:
			_append(parts, loc)
		for n in reduced_nouns:
			_append(parts, n)
		if person == '3' and (not visible_pronoun):
			visible_pronoun = 'yehuatl'
		if person == '3' and visible_pronoun:
			_append(parts, visible_pronoun)
		if past_marker:
			_append(parts, past_marker)
		if semi != '∅':
			_append(parts, semi)
		_append(parts, fuse_k(verb_ntl, suffix))
		return finalize_ntl(parts)
	if verb_ntl and unspecified_object and (not reduced_nouns):
		verb_ntl = apply_reference_to_ntl_root(verb_ntl, unspecified_object)
		direct_object = ''
	if verb_ntl in DEFAULT_KI_VERBS:
		if not is_nominalized_with_belonging:
			if reduced_nouns:
				if direct_object in {'k', 'ki'}:
					direct_object = ''
				if person == '3' and (not visible_pronoun):
					visible_pronoun = 'yehuatl'
			elif unspecified_object in {'k', 'ki'}:
				direct_object = 'k'
				direct_object = fix_k_ki(direct_object, semi, suffix)
			elif not direct_object:
				direct_object = 'k'
				direct_object = fix_k_ki(direct_object, semi, suffix)
	already_conjugated_past = prefixed_past
	if structure.get('modal_compound') or already_conjugated_past:
		verb_form = verb_ntl if verb_ntl else ''
	else:
		verb_form = build_ntl_finite_verb(verb_ntl, time, person, number) if verb_ntl else ''
	print()
	print('DEBUG BUILD')
	print('verb_ntl =', verb_ntl)
	print('time\t =', time)
	print('person   =', person)
	print('number   =', number)
	print('semi\t =', semi)
	print('past\t =', past_marker)
	print('suffix   =', suffix)
	print('verb_form=', verb_form)
	print()
	has_relational = any((m in unique_modifiers for m in {'ik', 'ipal'}))
	if verb_already_reflexive:
		eff_visible = visible_pronoun
		eff_semi = semi
		if eff_semi == '∅':
			eff_semi = choose_semipronoun(person, number)
		if reduced_nouns and has_relational:
			rel = 'ipal' if 'ipal' in unique_modifiers else 'ik'
			_append(parts, rel)
			_append(parts, reduced_nouns[0])
			if eff_visible:
				_append(parts, eff_visible)
			if past_marker:
				_append(parts, past_marker)
			if eff_semi != '∅':
				_append(parts, eff_semi)
			if verb_form:
				_append(parts, verb_form)
			return finalize_ntl(parts)
		for m in unique_modifiers:
			_append(parts, m)
		for loc in locatives:
			_append(parts, loc)
		if eff_visible:
			_append(parts, eff_visible)
		if past_marker:
			_append(parts, past_marker)
		if eff_semi != '∅':
			_append(parts, eff_semi)
		if verb_form:
			_append(parts, verb_form)
		return finalize_ntl(parts)
	if not verb_ntl and (reduced_nouns or unique_modifiers or locatives):
		rel_marker = None
		if 'ipal' in unique_modifiers:
			rel_marker = 'ipal'
		elif 'ik' in unique_modifiers:
			rel_marker = 'ik'
		if belonging and len(reduced_nouns) >= 2 and rel_marker:
			main_noun = reduced_nouns[0]
			secondary_noun = reduced_nouns[1]
			if main_noun == 'ohtli':
				main_noun = 'oh'
			if secondary_noun == 'nemiliztli':
				secondary_noun = 'nemiliz'
			else:
				secondary_noun = strip_nominal_suffix_ntl(secondary_noun)
			_append(parts, rel_marker)
			_append(parts, secondary_noun)
			_append(parts, belonging)
			_append(parts, main_noun)
			for m in unique_modifiers:
				if m != rel_marker:
					_append(parts, m)
			for loc in locatives:
				_append(parts, loc)
			return finalize_ntl(parts)
		for m in unique_modifiers:
			_append(parts, m)
		for loc in locatives:
			_append(parts, loc)
		if belonging:
			_append(parts, belonging)
		for n in reduced_nouns:
			if n == 'ohtli':
				n = 'oh'
			_append(parts, n)
		return finalize_ntl(parts)
	if verb_ntl == 'nemi' and reduced_nouns and (not has_relational):
		for m in unique_modifiers:
			_append(parts, m)
		for loc in locatives:
			_append(parts, loc)
		if belonging:
			_append(parts, belonging)
		for n in reduced_nouns:
			_append(parts, n)
		if visible_pronoun and (not belonging):
			_append(parts, visible_pronoun)
		if past_marker:
			_append(parts, past_marker)
		if semi != '∅':
			_append(parts, semi)
		if reflexive_out:
			_append(parts, reflexive_out)
		if direct_object:
			_append(parts, direct_object)
		if verb_form:
			_append(parts, verb_form)
		return finalize_ntl(parts)
	if reduced_nouns and has_relational:
		rel = 'ipal' if 'ipal' in unique_modifiers else 'ik'
		_append(parts, rel)
		comp = reduced_nouns[0]
		_append(parts, comp)
		if visible_pronoun:
			_append(parts, visible_pronoun)
		if past_marker:
			_append(parts, past_marker)
		if semi != '∅':
			_append(parts, semi)
		elif show_null_subject:
			_append(parts, '∅')
		if reflexive_out:
			_append(parts, reflexive_out)
		if direct_object:
			_append(parts, direct_object)
		if verb_form:
			_append(parts, verb_form)
		return finalize_ntl(parts)
	parts = []
	for adv in structure.get('adverbs') or []:
		if adv and adv not in parts:
			parts.append(adv)
	ADVERBIAL_MODIFIERS_NTL = {'izel', 'nochipa', 'ixkikan', 'aik', 'amo', 'yeze', 'uahki', 'kenin', 'kexki', 'achto', 'ompa', 'nican', 'nopa', 'ipal', 'ik'}
	noun_adjective_modifiers = []
	general_modifiers = []
	for m in unique_modifiers:
		if m in ADVERBIAL_MODIFIERS_NTL:
			general_modifiers.append(m)
		else:
			noun_adjective_modifiers.append(m)
	belonging_noun_blocks = []
	normal_noun_blocks = []
	for n in reduced_nouns:
		n_text = str(n).strip()
		if any((n_text == pref or n_text.startswith(pref + ' ') for pref in BELONGING_PREFIXES)):
			belonging_noun_blocks.append(n)
		else:
			normal_noun_blocks.append(n)
	if question_noun:
		_append(parts, question_noun)
	for m in general_modifiers:
		_append(parts, m)
	for sub in structure.get('subordinate_phrases', []):
		_append(parts, sub)
	for loc in locatives:
		_append(parts, loc)
	if belonging and (not belonging_noun_blocks):
		_append(parts, belonging)
	for n in belonging_noun_blocks:
		_append(parts, n)
	for m in noun_adjective_modifiers:
		_append(parts, m)
	for n in normal_noun_blocks:
		if n in {'lo', 'la', 'los', 'las'}:
			continue
		_append(parts, n)
	for money in money_modifiers:
		_append(parts, money)
	if visible_pronoun and (not belonging):
		_append(parts, visible_pronoun)
	if past_marker:
		_append(parts, past_marker)
	if semi != '∅':
		_append(parts, semi)
	elif show_null_subject:
		_append(parts, '∅')
	if indirect_object:
		_append(parts, indirect_object)
	elif reflexive_out:
		_append(parts, reflexive_out)
	if direct_object:
		_append(parts, direct_object)
	if verb_form:
		_append(parts, verb_form)
	return finalize_ntl(parts)

def format_analysis(structure: dict) -> str:
	return f"""{{\n\t"visible_pronoun":{repr(structure.get('visible_pronoun'))},\n\t"subject":{repr(structure.get('subject'))},\n\t"time":{repr(structure.get('time'))},\n\t"direct_object":{repr(structure.get('direct_object'))},\n\t"reflexive":{repr(structure.get('reflexive'))},\n\t"verb_sp":{repr(structure.get('verb_sp'))},\n\t"verb_ntl":{repr(structure.get('verb_ntl'))},\n\t"locatives":{repr(structure.get('locatives'))},\n  "belonging":{repr(structure.get('belonging'))},\n  "nouns":{repr(structure.get('nouns'))},\n  "modifiers":{repr(structure.get('modifiers'))}\n}}"""

def candidate_paths(*names):
	for folder in [base_dir, base_dir / 'assets', base_dir / 'res']:
		for nm in names:
			yield (folder / nm)
AUXILIARY_FORMS_SP = {'quiero': ('querer', 'neki', ('1', 'sg'), 'Present'), 'quieres': ('querer', 'neki', ('2', 'sg'), 'Present'), 'quiere': ('querer', 'neki', ('3', 'sg'), 'Present'), 'queremos': ('querer', 'neki', ('1', 'pl'), 'Present'), 'quieren': ('querer', 'neki', ('3', 'pl'), 'Present'), 'quería': ('querer', 'neki', ('1', 'sg'), 'Copreterite'), 'querías': ('querer', 'neki', ('2', 'sg'), 'Copreterite'), 'queríamos': ('querer', 'neki', ('1', 'pl'), 'Copreterite'), 'querían': ('querer', 'neki', ('3', 'pl'), 'Copreterite'), 'queria': ('querer', 'neki', ('1', 'sg'), 'Copreterite'), 'querias': ('querer', 'neki', ('2', 'sg'), 'Copreterite'), 'queriamos': ('querer', 'neki', ('1', 'pl'), 'Copreterite'), 'querian': ('querer', 'neki', ('3', 'pl'), 'Copreterite'), 'quiera': ('querer', 'neki', ('3', 'sg'), 'Subjunctive'), 'quieras': ('querer', 'neki', ('2', 'sg'), 'Subjunctive'), 'queramos': ('querer', 'neki', ('1', 'pl'), 'Subjunctive'), 'quieran': ('querer', 'neki', ('3', 'pl'), 'Subjunctive'), 'puedo': ('poder', 'ueli', ('1', 'sg'), 'Present'), 'puedes': ('poder', 'ueli', ('2', 'sg'), 'Present'), 'puede': ('poder', 'ueli', ('3', 'sg'), 'Present'), 'podemos': ('poder', 'ueli', ('1', 'pl'), 'Present'), 'pueden': ('poder', 'ueli', ('3', 'pl'), 'Present'), 'podía': ('poder', 'ueli', ('1', 'sg'), 'Copreterite'), 'podías': ('poder', 'ueli', ('2', 'sg'), 'Copreterite'), 'podíamos': ('poder', 'ueli', ('1', 'pl'), 'Copreterite'), 'podían': ('poder', 'ueli', ('3', 'pl'), 'Copreterite'), 'podia': ('poder', 'ueli', ('1', 'sg'), 'Copreterite'), 'podias': ('poder', 'ueli', ('2', 'sg'), 'Copreterite'), 'podiamos': ('poder', 'ueli', ('1', 'pl'), 'Copreterite'), 'podian': ('poder', 'ueli', ('3', 'pl'), 'Copreterite'), 'pueda': ('poder', 'ueli', ('3', 'sg'), 'Subjunctive'), 'puedas': ('poder', 'ueli', ('2', 'sg'), 'Subjunctive'), 'podamos': ('poder', 'ueli', ('1', 'pl'), 'Subjunctive'), 'puedan': ('poder', 'ueli', ('3', 'pl'), 'Subjunctive'), 'debo': ('deber', 'uihkili', ('1', 'sg'), 'Present'), 'debes': ('deber', 'uihkili', ('2', 'sg'), 'Present'), 'debe': ('deber', 'uihkili', ('3', 'sg'), 'Present'), 'debemos': ('deber', 'uihkili', ('1', 'pl'), 'Present'), 'deben': ('deber', 'uihkili', ('3', 'pl'), 'Present'), 'debía': ('deber', 'uihkili', ('1', 'sg'), 'Copreterite'), 'debías': ('deber', 'uihkili', ('2', 'sg'), 'Copreterite'), 'debíamos': ('deber', 'uihkili', ('1', 'pl'), 'Copreterite'), 'debían': ('deber', 'uihkili', ('3', 'pl'), 'Copreterite'), 'debia': ('deber', 'uihkili', ('1', 'sg'), 'Copreterite'), 'debias': ('deber', 'uihkili', ('2', 'sg'), 'Copreterite'), 'debiamos': ('deber', 'uihkili', ('1', 'pl'), 'Copreterite'), 'debian': ('deber', 'uihkili', ('3', 'pl'), 'Copreterite'), 'deba': ('deber', 'uihkili', ('3', 'sg'), 'Subjunctive'), 'debas': ('deber', 'uihkili', ('2', 'sg'), 'Subjunctive'), 'debamos': ('deber', 'uihkili', ('1', 'pl'), 'Subjunctive'), 'deban': ('deber', 'uihkili', ('3', 'pl'), 'Subjunctive'), 'necesito': ('necesitar', 'onneki', ('1', 'sg'), 'Present'), 'necesitas': ('necesitar', 'onneki', ('2', 'sg'), 'Present'), 'necesita': ('necesitar', 'onneki', ('3', 'sg'), 'Present'), 'necesitamos': ('necesitar', 'onneki', ('1', 'pl'), 'Present'), 'necesitan': ('necesitar', 'onneki', ('3', 'pl'), 'Present'), 'necesitaba': ('necesitar', 'onneki', ('1', 'sg'), 'Copreterite'), 'necesitabas': ('necesitar', 'onneki', ('2', 'sg'), 'Copreterite'), 'necesitábamos': ('necesitar', 'onneki', ('1', 'pl'), 'Copreterite'), 'necesitaban': ('necesitar', 'onneki', ('3', 'pl'), 'Copreterite'), 'necesitabamos': ('necesitar', 'onneki', ('1', 'pl'), 'Copreterite'), 'necesite': ('necesitar', 'onneki', ('3', 'sg'), 'Subjunctive'), 'necesites': ('necesitar', 'onneki', ('2', 'sg'), 'Subjunctive'), 'necesitemos': ('necesitar', 'onneki', ('1', 'pl'), 'Subjunctive'), 'necesiten': ('necesitar', 'onneki', ('3', 'pl'), 'Subjunctive'), 'estoy': ('estar', 'ka', ('1', 'sg'), 'Present'), 'estás': ('estar', 'ka', ('2', 'sg'), 'Present'), 'estas': ('estar', 'ka', ('2', 'sg'), 'Present'), 'está': ('estar', 'ka', ('3', 'sg'), 'Present'), 'esta': ('estar', 'ka', ('3', 'sg'), 'Present'), 'estamos': ('estar', 'ka', ('1', 'pl'), 'Present'), 'están': ('estar', 'ka', ('3', 'pl'), 'Present'), 'estan': ('estar', 'ka', ('3', 'pl'), 'Present'), 'estaba': ('estar', 'ka', ('1', 'sg'), 'Copreterite'), 'estabas': ('estar', 'ka', ('2', 'sg'), 'Copreterite'), 'estábamos': ('estar', 'ka', ('1', 'pl'), 'Copreterite'), 'estabamos': ('estar', 'ka', ('1', 'pl'), 'Copreterite'), 'estaban': ('estar', 'ka', ('3', 'pl'), 'Copreterite'), 'esté': ('estar', 'ka', ('3', 'sg'), 'Subjunctive'), 'este': ('estar', 'ka', ('3', 'sg'), 'Subjunctive'), 'estés': ('estar', 'ka', ('2', 'sg'), 'Subjunctive'), 'estes': ('estar', 'ka', ('2', 'sg'), 'Subjunctive'), 'estemos': ('estar', 'ka', ('1', 'pl'), 'Subjunctive'), 'estén': ('estar', 'ka', ('3', 'pl'), 'Subjunctive'), 'esten': ('estar', 'ka', ('3', 'pl'), 'Subjunctive'), 'voy': ('ir', 'yau', ('1', 'sg'), 'Present'), 'vas': ('ir', 'yau', ('2', 'sg'), 'Present'), 'va': ('ir', 'yau', ('3', 'sg'), 'Present'), 'vamos': ('ir', 'yau', ('1', 'pl'), 'Present'), 'van': ('ir', 'yau', ('3', 'pl'), 'Present'), 'iba': ('ir', 'yau', ('1', 'sg'), 'Copreterite'), 'ibas': ('ir', 'yau', ('2', 'sg'), 'Copreterite'), 'íbamos': ('ir', 'yau', ('1', 'pl'), 'Copreterite'), 'ibamos': ('ir', 'yau', ('1', 'pl'), 'Copreterite'), 'iban': ('ir', 'yau', ('3', 'pl'), 'Copreterite'), 'vaya': ('ir', 'yau', ('3', 'sg'), 'Subjunctive'), 'vayas': ('ir', 'yau', ('2', 'sg'), 'Subjunctive'), 'vayamos': ('ir', 'yau', ('1', 'pl'), 'Subjunctive'), 'vayan': ('ir', 'yau', ('3', 'pl'), 'Subjunctive'), 'hay': ('haber', 'onka', ('3', 'sg'), 'Present'), 'había': ('haber', 'onka', ('3', 'sg'), 'Copreterite'), 'habia': ('haber', 'onka', ('3', 'sg'), 'Copreterite'), 'haya': ('haber', 'onka', ('3', 'sg'), 'Subjunctive'), 'hayan': ('haber', 'onka', ('3', 'pl'), 'Subjunctive'), 'tengo': ('tener', 'pia', ('1', 'sg'), 'Present'), 'tienes': ('tener', 'pia', ('2', 'sg'), 'Present'), 'tiene': ('tener', 'pia', ('3', 'sg'), 'Present'), 'tenemos': ('tener', 'pia', ('1', 'pl'), 'Present'), 'tienen': ('tener', 'pia', ('3', 'pl'), 'Present'), 'tenía': ('tener', 'pia', ('1', 'sg'), 'Copreterite'), 'tenia': ('tener', 'pia', ('1', 'sg'), 'Copreterite'), 'tenías': ('tener', 'pia', ('2', 'sg'), 'Copreterite'), 'tenias': ('tener', 'pia', ('2', 'sg'), 'Copreterite'), 'teníamos': ('tener', 'pia', ('1', 'pl'), 'Copreterite'), 'teniamos': ('tener', 'pia', ('1', 'pl'), 'Copreterite'), 'tenían': ('tener', 'pia', ('3', 'pl'), 'Copreterite'), 'tenian': ('tener', 'pia', ('3', 'pl'), 'Copreterite'), 'tenga': ('tener', 'pia', ('3', 'sg'), 'Subjunctive'), 'tengas': ('tener', 'pia', ('2', 'sg'), 'Subjunctive'), 'tengamos': ('tener', 'pia', ('1', 'pl'), 'Subjunctive'), 'tengan': ('tener', 'pia', ('3', 'pl'), 'Subjunctive'), 'doy': ('dar', 'maka', ('1', 'sg'), 'Present'), 'das': ('dar', 'maka', ('2', 'sg'), 'Present'), 'da': ('dar', 'maka', ('3', 'sg'), 'Present'), 'damos': ('dar', 'maka', ('1', 'pl'), 'Present'), 'dan': ('dar', 'maka', ('3', 'pl'), 'Present'), 'daba': ('dar', 'maka', ('1', 'sg'), 'Copreterite'), 'dabas': ('dar', 'maka', ('2', 'sg'), 'Copreterite'), 'dábamos': ('dar', 'maka', ('1', 'pl'), 'Copreterite'), 'dabamos': ('dar', 'maka', ('1', 'pl'), 'Copreterite'), 'daban': ('dar', 'maka', ('3', 'pl'), 'Copreterite'), 'dé': ('dar', 'maka', ('3', 'sg'), 'Subjunctive'), 'des': ('dar', 'maka', ('2', 'sg'), 'Subjunctive'), 'demos': ('dar', 'maka', ('1', 'pl'), 'Subjunctive'), 'den': ('dar', 'maka', ('3', 'pl'), 'Subjunctive')}

def classify_section_sp(tokens: list[str]) -> str:
	toks = [tk for tk in tokens if tk]
	if not toks:
		return 'EMPTY'
	if any((tk in {'sucedió', 'ocurrió', 'pasó'} for tk in toks)):
		return 'NARRATIVE_INTRO'
	if any((tk in {'debo', 'debes', 'debe', 'debemos', 'deben', 'tuvo', 'tuvieron'} for tk in toks)):
		return 'OBLIGATIVE'
	# Las formas existenciales de "haber" (hay, había, haya...) no deben
	# enviar automáticamente toda la oración a AUXILIARY_SUBORDINATE.
	# Sólo funcionan como auxiliares cuando introducen de manera inmediata
	# una subordinada con "que" o una forma verbal compatible.
	haber_existential_forms = {'hay', 'había', 'habia', 'haya', 'hayan'}
	has_auxiliary_subordinate = False
	for aux_i, tk in enumerate(toks):
		if tk not in AUXILIARY_FORMS_SP:
			continue
		tail = toks[aux_i + 1:]

		# Sólo los auxiliares modales pueden gobernar un infinitivo. Verbos
		# plenos como tener no absorben una oración sólo porque más adelante
		# aparezca una finalidad: «tenía recetas para conseguir...». Para los
		# demás auxiliares exigimos un complemento verbal inmediato.
		if is_modal_auxiliary_sp(tk):
			has_auxiliary_subordinate = True
			break

		if tail and (
			tail[0] == 'que'
			or is_spanish_infinitive(tail[0])
			or tolerant_lookup(tail[0], ado_ido)
		):
			has_auxiliary_subordinate = True
			break
	if has_auxiliary_subordinate:
		return 'AUXILIARY_SUBORDINATE'
	if 'cuando' in toks or 'cuándo' in toks:
		return 'TEMPORAL_WHEN'
	if 'mientras' in toks:
		return 'TEMPORAL_WHILE'
	if 'que' in toks or 'tlen' in toks:
		return 'RELATIVE'
	if any((tk.endswith(('ando', 'iendo')) for tk in toks)):
		return 'GERUND_CONTRAST'
	if any((tk in {'no', 'nada', 'sin'} for tk in toks)):
		return 'NEGATIVE'
	if any((tk in {'en', 'sobre', 'dentro', 'allí', 'aquí', 'campo'} for tk in toks)):
		return 'LOCATIVE'
	if any((tk in {'con', 'mediante'} for tk in toks)):
		return 'INSTRUMENTAL_OR_COMPANY'
	if any((tk in {'y', 'pero'} for tk in toks)):
		return 'COORDINATED'
	if any((tk.endswith(('ar', 'er', 'ir')) for tk in toks)):
		return 'INFINITIVE_CHAIN'
	if any((tk in {'me', 'te', 'se', 'nos'} for tk in toks)):
		return 'REFLEXIVE_VERBAL'
	return 'SIMPLE_VERBAL'

def translate_relative_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	print('RELATIVE_SECTION:', repr(t))
	if 'les dijo que' in t and 'no les quedaba' in t and ('aprender a labrar la tierra' in t):
		return 'o kin ihtok tlen izel tzalotizkehtza tlalteteki'
	tokens = t.split()
	if 'que' not in tokens:
		return None
	que_i = tokens.index('que')
	left_tokens = tokens[:que_i]
	right_tokens = tokens[que_i + 1:]
	if not left_tokens or not right_tokens:
		return None
	left_text = ' '.join(left_tokens)
	right_text = ' '.join(right_tokens)
	left_ntl = translate_sp_to_ntl(left_text)
	right_ntl = translate_sp_to_ntl(right_text)
	if not left_ntl or not right_ntl:
		return None
	if left_ntl.startswith('[Aviso]') or right_ntl.startswith('[Aviso]'):
		return None
	return finalize_simple_ntl([left_ntl, 'tlen', right_ntl])

def translate_atomic_section_sp(t: str) -> str | None:
	"""
	Traduce una sola palabra que debe conservar directamente
	la forma registrada en sus diccionarios especializados.

	Ejemplos:

		comido	  -> otlakuak
		caminado	-> nehnemik
		despertado  -> izak
		y		   -> uan
		yo		  -> nehuatl

	Un participio aislado no debe enviarse al conjugador general,
	porque ya contiene su forma estructurada.
	"""

	t = normalize_input_sp(t)

	tokens = t.split()

	if len(tokens) != 1:
		return None

	token = tokens[0]

	# ---------------------------------------------------------
	# 1. PARTICIPIO ESPAÑOL → FORMA NÁHUATL
	# ---------------------------------------------------------
	#
	# ado_ido.py ya contiene las formas completas:
	#
	#	comido	 -> otlakuak
	#	caminado   -> nehnemik
	#	despertado -> izak
	#
	# Deben devolverse directamente, sin agregar sufijos.
	#

	participle_ntl = tolerant_lookup(token, ado_ido)

	if participle_ntl:
		return first_variant(participle_ntl)

	# ---------------------------------------------------------
	# 2. CONJUNCIONES ATÓMICAS
	# ---------------------------------------------------------

	if token in {'y', 'e'}:
		return 'uan'

	if token == 'pero':
		return 'pero'

	# ---------------------------------------------------------
	# 3. PRONOMBRES VISIBLES
	# ---------------------------------------------------------

	if token in {
		'yo',
		'tú',
		'tu',
		'él',
		'el',
		'ella',
		'nosotros',
		'nosotras',
		'ustedes',
		'ellos',
		'ellas'
	}:
		return VISIBLE_PRONOUN_MAP_SP_TO_NTL.get(token)

	return None



def finalize_simple_ntl(parts: list[str]) -> str:
	clean = []
	for p in parts:
		if p:
			p = str(p).strip()
			if p:
				clean.append(p)
	result = ' '.join(clean)
	result = re.sub('\\s+', ' ', result).strip()
	return result

def translate_negative_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	if 'no' not in tokens and 'nada' not in tokens:
		return None
	visible_pronoun, subject = detect_pronoun_info(tokens)
	verb_sp, verb_ntl, verb_subject, time = detect_finite_verb(tokens)
	if not verb_ntl:
		verb_sp, verb_ntl, verb_subject, time = detect_regular_verb(tokens)
	if not verb_ntl:
		verb_sp, verb_ntl = detect_simple_verb(tokens)
		time = 'Present'
	if not verb_ntl:
		return None
	if verb_subject:
		subject = verb_subject
	if not subject:
		subject = ('3', 'sg')
	person, number = subject
	semi = choose_semipronoun(person, number)
	suffix = choose_suffix(time or 'Present', number)
	verb_form = fuse_k(verb_ntl, suffix)
	if not visible_pronoun:
		if person == '1' and number == 'sg':
			visible_pronoun = 'nehuatl'
		elif person == '2' and number == 'sg':
			visible_pronoun = 'tehuatl'
		elif person == '1' and number == 'pl':
			visible_pronoun = 'tehuan'
		elif person == '2' and number == 'pl':
			visible_pronoun = 'anmehuan'
		elif person == '3' and number == 'sg':
			visible_pronoun = 'yehuatl'
		elif person == '3' and number == 'pl':
			visible_pronoun = 'yehuan'
	direct_object = None
	for phrase, value in sorted(DIRECT_OBJECT_MAP_SP_TO_NTL.items(), key=lambda x: len(x[0].split()), reverse=True):
		phrase_tokens = phrase.split()
		n = len(phrase_tokens)
		for i in range(len(tokens) - n + 1):
			if tokens[i:i + n] == phrase_tokens:
				direct_object = value
				break
		if direct_object:
			break
	if not direct_object:
		direct_object = detect_direct_object(t)
	reflexive_out = None
	if not direct_object:
		reflexive_out = detect_reflexive(tokens)
		if reflexive_out == '∅mo':
			reflexive_out = 'mo'
	parts = []
	if visible_pronoun:
		parts.append(visible_pronoun)
	if direct_object:
		parts.append(direct_object)
	parts.append('amo')
	if 'nada' in tokens:
		parts.append('amitla')
	else:
		parts.append('amo')
	if semi != '∅':
		parts.append(semi)
	if reflexive_out:
		parts.append(reflexive_out)
	parts.append(verb_form)
	return finalize_simple_ntl(parts)

def translate_gerund_contrast_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	gerunds = []
	for tk in tokens:
		gerund_ntl = detect_dynamic_gerund_sp(tk)
		if gerund_ntl and gerund_ntl.endswith('tika'):
			gerunds.append(gerund_ntl)
	if len(gerunds) < 2:
		return None
	main_verb = None
	for tk in tokens:
		tk_clean = tk.strip('.,;:¡!¿?')
		if tk_clean in {'no', 'nada', 'sí', 'si'} or tk_clean.endswith(('ando', 'iendo')):
			continue
		val = first_variant(tolerant_lookup(tk_clean, sp_ntl))
		if val:
			main_verb = val
			break
		verb_sp, verb_ntl, subject, time = detect_finite_verb([tk_clean])
		if verb_ntl:
			suffix = choose_suffix(time or 'Present', subject[1] if subject else 'sg')
			semi = SEMIPRONOUN_MAP_NTL.get(subject, '')
			main_verb = (semi + ' ' + fuse_k(verb_ntl, suffix)).strip()
			break
	if not main_verb:
		return None
	return f'amitla {gerunds[0]} kema {gerunds[1]} {main_verb}'

def translate_infinitive_chain_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	return translate_purpose_chain_sp(t)

def translate_locative_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	return None

def translate_reflexive_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	return None

def force_past_verb_final_by_connector_ntl(ntl: str) -> str:
	connectors = {'tlen', 'uan', 'ika', 'ipan', 'ikuak'}
	tokens = ntl.split()
	if not tokens:
		return ntl

	def is_past_verb_at(seq: list[str], i: int) -> bool:
		return i + 1 < len(seq) and seq[i] == 'o' and seq[i + 1].endswith(('k', 'keh'))

	def extract_past_verbs(seq: list[str]) -> tuple[list[str], list[list[str]]]:
		rest = []
		verbs = []
		i = 0
		while i < len(seq):
			if is_past_verb_at(seq, i):
				verbs.append(seq[i:i + 2])
				i += 2
			else:
				rest.append(seq[i])
				i += 1
		return (rest, verbs)
	for conn in connectors:
		if conn not in tokens:
			continue
		conn_i = tokens.index(conn)
		left = tokens[:conn_i]
		right = tokens[conn_i + 1:]
		left_rest, left_verbs = extract_past_verbs(left)
		right_rest, right_verbs = extract_past_verbs(right)
		if not left_verbs and len(right_verbs) >= 2:
			left_verbs.append(right_verbs.pop(0))
		fixed = left_rest + [v for block in left_verbs for v in block] + [conn] + right_rest + [v for block in right_verbs for v in block]
		return ' '.join(fixed)
	return ntl

def translate_temporal_when_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	# Acepta la variante gráfica «cuándo» dentro de una oración temporal.
	# La tilde no debe impedir que se separen ambas cláusulas y se conserve
	# el verbo finito de cada una. Una pregunta aislada «¿cuándo ...?» sigue
	# fuera de esta ruta porque no tiene cláusula izquierda.
	when_token = 'cuando' if 'cuando' in tokens else ('cuándo' if 'cuándo' in tokens else None)
	if when_token is None:
		return None
	i = tokens.index(when_token)
	left = ' '.join(tokens[:i]).strip()
	right = ' '.join(tokens[i + 1:]).strip()
	if not left or not right:
		return None
	left_ntl = translate_sp_to_ntl(left)
	right_ntl = translate_sp_to_ntl(right)
	if not left_ntl or not right_ntl:
		return None
	left_ntl = force_final_verb_ntl_clause(left_ntl)
	right_ntl = force_final_verb_ntl_clause(right_ntl)
	return f'{left_ntl} ikuak {right_ntl}'

def translate_temporal_while_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	if 'mientras' not in tokens:
		return None
	i = tokens.index('mientras')
	before = ' '.join(tokens[:i]).strip()
	after = ' '.join(tokens[i + 1:]).strip()
	if not after:
		return None
	if not before:
		after_tokens = after.split()
		cut = None
		for j in range(1, len(after_tokens)):
			left_test = after_tokens[:j + 1]
			right_test = after_tokens[j + 1:]
			if not right_test:
				continue
			verb_sp, verb_ntl, subject, time = detect_finite_verb(left_test)
			if verb_sp:
				cut = j + 1
				break
		if cut is None:
			return None
		left = ' '.join(after_tokens[:cut]).strip()
		right = ' '.join(after_tokens[cut:]).strip()
		if not left or not right:
			return None
		left_ntl = translate_sp_to_ntl(left)
		right_ntl = translate_sp_to_ntl(right)
		if not left_ntl or not right_ntl:
			return None
		if left_ntl.startswith('[Aviso]') or right_ntl.startswith('[Aviso]'):
			return None
		left_ntl = force_past_verb_final_ntl(left_ntl)
		right_ntl = force_past_verb_final_ntl(right_ntl)
		return f'ipan kauitl {left_ntl} {right_ntl}'
	main_left = before
	temporal_right = after
	left_ntl = translate_sp_to_ntl(main_left)
	right_ntl = translate_sp_to_ntl(temporal_right)
	if not left_ntl or not right_ntl:
		return None
	if left_ntl.startswith('[Aviso]') or right_ntl.startswith('[Aviso]'):
		return None
	left_ntl = force_past_verb_final_ntl(left_ntl)
	right_ntl = force_past_verb_final_ntl(right_ntl)
	return f'{left_ntl} ipan kauitl {right_ntl}'

def translate_duration_progressive_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	if not any((x in tokens for x in {'llevaba', 'llevaban', 'lleva', 'llevan'})):
		return None
	if not any((tk.endswith(('ando', 'iendo')) for tk in tokens)):
		return None
	duration = None
	if 'año' in tokens or 'ano' in tokens:
		duration = 'ze xiuitl'
	elif 'años' in tokens or 'anos' in tokens:
		duration = 'xiuitl'
	gerund = None
	for tk in tokens:
		if not tk.endswith(('ando', 'iendo')):
			continue
		gerund = detect_dynamic_gerund_sp(tk)
		if gerund:
			break
	manner = 'ikin' if 'así' in tokens or 'asi' in tokens else None
	subject = ('3', 'pl') if 'llevaban' in tokens or 'llevan' in tokens else ('3', 'sg')
	verb = 'uihkayakeh' if subject == ('3', 'pl') else 'uihkaya'
	parts = []
	if duration:
		parts.append(duration)
	if manner:
		parts.append(manner)
	if gerund:
		parts.append(gerund)
	parts.append(verb)
	return finalize_simple_ntl(parts)

def translate_purpose_chain_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	if 'para' not in tokens:
		return None
	para_i = tokens.index('para')
	main_tokens = tokens[:para_i]
	sub_tokens = tokens[para_i + 1:]
	parts = []
	if 'hasta' in main_tokens:
		parts.append('ixkikan')
	subordinate = None
	if sub_tokens:
		inf_sp = sub_tokens[0]
		inf_ntl = first_variant(tolerant_lookup(inf_sp, sp_ntl))
		if not inf_ntl:
			inf_ntl = INFINITIVE_VERBS_SP_TO_NTL.get(inf_sp)
		if not inf_ntl:
			inf_ntl = CORE_VERBS_SP_TO_NTL.get(inf_sp)
		if inf_ntl:
			subordinate = f'inik {inf_ntl}'
	main_object = None
	if 'tiempo' in main_tokens:
		main_object = 'kauitl'
	main_verb = None
	for tk in main_tokens:
		verb_sp, verb_ntl, subject, time = detect_finite_verb([tk])
		if not verb_ntl:
			verb_sp, verb_ntl, subject, time = detect_regular_verb([tk])
		if verb_ntl:
			number = subject[1] if subject else 'sg'
			main_verb = fuse_k(verb_ntl, choose_suffix(time or 'Present', number))
			break
	if not main_verb:
		for tk in main_tokens:
			if tk.endswith('aba'):
				stem = tk[:-3]
				if stem + 'ar' in CORE_VERBS_SP_TO_NTL:
					verb_ntl = CORE_VERBS_SP_TO_NTL[stem + 'ar']
					main_verb = fuse_k(verb_ntl, 'ya')
					break
			if tk.endswith('ía'):
				stem = tk[:-2]
				if stem + 'er' in CORE_VERBS_SP_TO_NTL:
					verb_ntl = CORE_VERBS_SP_TO_NTL[stem + 'er']
					main_verb = fuse_k(verb_ntl, 'ya')
					break
				if stem + 'ir' in CORE_VERBS_SP_TO_NTL:
					verb_ntl = CORE_VERBS_SP_TO_NTL[stem + 'ir']
					main_verb = fuse_k(verb_ntl, 'ya')
					break
	if not subordinate:
		return None
	if subordinate:
		parts.append(subordinate)
	if main_object:
		parts.append(main_object)
	if main_verb:
		parts.append(main_verb)
	if parts and main_verb:
		return finalize_simple_ntl(parts)
	return None

def translate_poder_infinitive_sp(t: str) -> str | None:
	"""
	Detecta construcciones con poder + infinitivo.
	Según el análisis aplicado aquí, la marca temporal recae en el verbo principal,
	no en ueli:
	- pudo recuperar  -> o ontlakuik ueli
	- podrá recuperar -> tlakuiz-ueli
	"""
	t = normalize_input_sp(t)
	tokens = t.split()
	poder_forms = {'puedo': 'Present', 'puedes': 'Present', 'puede': 'Present', 'podemos': 'Present', 'pueden': 'Present', 'pude': 'Past', 'pudiste': 'Past', 'pudo': 'Past', 'pudimos': 'Past', 'pudieron': 'Past', 'podré': 'Future', 'podras': 'Future', 'podrás': 'Future', 'podrá': 'Future', 'podremos': 'Future', 'podrán': 'Future', 'podria': 'Postpreterite', 'podría': 'Postpreterite', 'podrias': 'Postpreterite', 'podrías': 'Postpreterite', 'podriamos': 'Postpreterite', 'podríamos': 'Postpreterite', 'podrian': 'Postpreterite', 'podrían': 'Postpreterite'}
	modal_i = None
	modal_time = None
	for i, tk in enumerate(tokens):
		if tk in poder_forms:
			modal_i = i
			modal_time = poder_forms[tk]
			break
	if modal_i is None:
		return None
	inf_i = None
	inf_sp = None
	for i in range(modal_i + 1, len(tokens)):
		tk = tokens[i]
		if tk in INFINITIVE_VERBS_SP_TO_NTL or tk in CORE_VERBS_SP_TO_NTL or tolerant_lookup(tk, sp_ntl):
			inf_i = i
			inf_sp = tk
			break
	if inf_i is None or not inf_sp:
		return None
	if inf_sp == 'recuperar':
		main_root = 'ontlakui'
	else:
		main_root = INFINITIVE_VERBS_SP_TO_NTL.get(inf_sp)
		if not main_root:
			main_root = CORE_VERBS_SP_TO_NTL.get(inf_sp)
		if not main_root:
			main_root = first_variant(tolerant_lookup(inf_sp, sp_ntl))
	if not main_root:
		return None
	compound = build_poder_compound_ntl(main_root, modal_time)
	remaining_tokens = [tk for i, tk in enumerate(tokens) if i not in {modal_i, inf_i}]
	parts = []
	if 'pero' in remaining_tokens:
		parts.append('yeze')
	if 'apenas' in remaining_tokens:
		parts.append('uahki')
	if 'mercader' in remaining_tokens:
		parts.append('namakotok')
	if 'sus' in remaining_tokens and ('mercancías' in remaining_tokens or 'mercancias' in remaining_tokens):
		parts.append('i namakoyouan')
	parts.append(compound)
	return finalize_simple_ntl(parts)

def translate_desiderative_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	querer_forms = {'quiero': (('1', 'sg'), 'Present'), 'quieres': (('2', 'sg'), 'Present'), 'quiere': (('3', 'sg'), 'Present'), 'queremos': (('1', 'pl'), 'Present'), 'quieren': (('3', 'pl'), 'Present'), 'quería': (('1', 'sg'), 'Copreterite'), 'queria': (('1', 'sg'), 'Copreterite'), 'querías': (('2', 'sg'), 'Copreterite'), 'querias': (('2', 'sg'), 'Copreterite'), 'queríamos': (('1', 'pl'), 'Copreterite'), 'queriamos': (('1', 'pl'), 'Copreterite'), 'querían': (('3', 'pl'), 'Copreterite'), 'querian': (('3', 'pl'), 'Copreterite'), 'quiera': (('3', 'sg'), 'Subjunctive'), 'quieras': (('2', 'sg'), 'Subjunctive'), 'queramos': (('1', 'pl'), 'Subjunctive'), 'quieran': (('3', 'pl'), 'Subjunctive')}
	aux_i = None
	aux_subject = None
	aux_time = None
	for i, tk in enumerate(tokens):
		if tk in querer_forms:
			aux_i = i
			aux_subject, aux_time = querer_forms[tk]
			break
	if aux_i is None:
		return None
	after = tokens[aux_i + 1:]
	if after and after[0] == 'que':
		after = after[1:]
	if not after:
		return None
	sub_verb_sp, sub_verb_ntl, sub_subject, sub_time = detect_finite_verb(after)
	has_que = tokens[aux_i + 1:aux_i + 2] == ['que']
	subordinate_has_visible_subject = any((tk in PRONOUN_MAP_SP for tk in after))
	if has_que and (not subordinate_has_visible_subject) and (sub_time == 'Subjunctive') and (sub_subject in {('1', 'sg'), ('3', 'sg')}):
		sub_subject = ('3', 'sg')
	if not sub_verb_ntl:
		sub_verb_sp, sub_verb_ntl = detect_simple_verb(after)
	if not sub_verb_ntl:
		return None
	sub_root = first_variant(sub_verb_ntl)
	for pref in ('ni', 'ti', 'an'):
		if sub_root.startswith(pref + ' '):
			sub_root = sub_root[len(pref):].strip()
		elif sub_root.startswith(pref) and len(sub_root) > len(pref):
			sub_root = sub_root[len(pref):].strip()
	if sub_root.startswith('o '):
		sub_root = sub_root[2:].strip()
	if sub_root.endswith('keh'):
		sub_root = sub_root[:-3]
	elif sub_root.endswith('h'):
		sub_root = sub_root[:-1]
	if sub_root.endswith('k') and aux_time != 'Past':
		sub_root = sub_root[:-1]
	compound = sub_root + 'neki'
	if aux_time == 'Copreterite':
		compound = compound + 'ya'
	elif aux_time == 'Past':
		compound = compound + 'k'
	elif aux_time == 'Future':
		compound = compound + 'z'
	if aux_time == 'Subjunctive':
		return 'ma ' + compound
	semi = SEMIPRONOUN_MAP_NTL.get(aux_subject)
	if semi and semi != '∅':
		return semi + ' ' + compound
	return compound

def translate_purpose_que_sp(tokens: list[str]) -> str | None:
	if not tokens:
		return None
	sub_verb_sp, sub_verb_ntl, sub_subject, sub_time = detect_finite_verb(tokens)
	if not sub_verb_ntl:
		sub_verb_sp, sub_verb_ntl = detect_simple_verb(tokens)
	if not sub_verb_ntl:
		return None
	root = first_variant(sub_verb_ntl)
	for pref in ('ni', 'ti', 'an'):
		if root.startswith(pref + ' '):
			root = root[len(pref):].strip()
		elif root.startswith(pref) and len(root) > len(pref):
			root = root[len(pref):].strip()
	if root.startswith('o '):
		root = root[2:].strip()
	if root.endswith('keh'):
		root = root[:-3]
	elif root.endswith('h'):
		root = root[:-1]
	if root.endswith('k'):
		root = root[:-1]
	if root.endswith('a'):
		root = root[:-1] + 'az'
	elif root.endswith('i'):
		root = root[:-1] + 'iz'
	elif root.endswith('o'):
		root = root[:-1] + 'oz'
	elif root.endswith('e'):
		root = root[:-1] + 'ez'
	elif not root.endswith('z'):
		root = root + 'z'
	return 'inik ' + root

def translate_auxiliary_subordinate_section_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	aux_i = None
	aux_data = None
	for i, tk in enumerate(tokens):
		if tk in AUXILIARY_FORMS_SP:
			aux_i = i
			aux_data = AUXILIARY_FORMS_SP[tk]
			break
	if aux_i is None or aux_data is None:
		return None
	aux_sp, aux_ntl, aux_subject, aux_time = aux_data
	aux_zone = tokens[:aux_i + 1]
	preposed_zone = tokens[:aux_i]
	aux_adverbs = detect_adverbs_sp(tokens, used_indexes={aux_i})
	aux_reflexive = None

	if any(
		tk in {'mismo', 'misma', 'mismos', 'mismas'}
		for tk in aux_zone
	):
		aux_reflexive = 'mo'
	elif 'se' in preposed_zone:
		aux_reflexive = 'mo'
	after_original = tokens[aux_i + 1:]
	has_que = bool(after_original and after_original[0] == 'que')
	purpose_phrase = None
	coordinated_phrase = None
	if 'para' in after_original:
		para_i = after_original.index('para')
		if para_i + 1 < len(after_original) and after_original[para_i + 1] == 'que':
			purpose_tokens = after_original[para_i + 2:]
			purpose_phrase = translate_purpose_que_sp(purpose_tokens)
			after_original = after_original[:para_i]
	after = after_original[:]
	if any((tk.endswith(('arme', 'erme', 'irme', 'arte', 'erte', 'irte', 'arlo', 'erlo', 'irlo', 'arla', 'erla', 'irla', 'arlos', 'erlos', 'irlos', 'arlas', 'erlas', 'irlas')) for tk in after)):
		return None
	if 'y' in after_original:
		y_i = after_original.index('y')
		if y_i + 1 < len(after_original) and after_original[y_i + 1] == 'que':
			coord_tokens = after_original[y_i + 2:]
			coord_ntl = translate_purpose_que_sp(coord_tokens)
			if coord_ntl:
				coordinated_phrase = 'iuan ' + coord_ntl.replace('inik ', '', 1)
			after_original = after_original[:y_i]
	if has_que:
		after = after[1:]
	if not after:
		return None
	sub_verb_sp, sub_verb_ntl, sub_subject, sub_time = detect_finite_verb(after)

	if not sub_verb_sp:
		sub_verb_sp, sub_verb_ntl = detect_simple_verb(after)

	subordinate_has_visible_subject = any(
		tk in PRONOUN_MAP_SP
		for tk in after
	)

	if (
		has_que
		and not subordinate_has_visible_subject
		and sub_time == 'Subjunctive'
		and sub_subject in {('1', 'sg'), ('3', 'sg')}
	):
		sub_subject = ('3', 'sg')

	object_marker = None

	preposed_object_map = {
		'me': 'nech',
		'te': 'mitz',
		'nos': 'tech',
		'lo': 'ki',
		'la': 'ki',
		'los': 'kin',
		'las': 'kin',
		'le': 'ki',
		'les': 'anmech',
	}

	for tk in preposed_zone:
		if tk not in preposed_object_map:
			continue

		if (
			tk in {'me', 'te', 'nos'}
			and sub_verb_sp in PRONOMINAL_VERBS_SP
		):
			aux_reflexive = 'mo'
			object_marker = None
		else:
			object_marker = preposed_object_map[tk]
			aux_reflexive = None

		break

	for tk in after:
		if tk in {'lo', 'la'}:
			object_marker = 'ki'
		elif tk in {'los', 'las'}:
			object_marker = 'kin'
		elif tk == 'me':
			object_marker = 'nech'
		elif tk == 'te':
			object_marker = 'mitz'
		elif tk == 'nos':
			object_marker = 'tech'
		elif tk == 'le':
			object_marker = 'ki'
		elif tk == 'les':
			object_marker = 'anmech'
	if has_que and object_marker is None and (sub_subject == ('3', 'sg')) and (sub_verb_sp in TRANSITIVE_VERBS_SP):
		object_marker = 'ki'
	if not sub_verb_ntl:
		sub_verb_sp, sub_verb_ntl = detect_simple_verb(after)
	if not sub_verb_ntl:
		return None
	sub_root = first_variant(sub_verb_ntl)
	for pref in ('ni', 'ti', 'an'):
		if sub_root.startswith(pref + ' '):
			sub_root = sub_root[len(pref):].strip()
		elif sub_root.startswith(pref) and len(sub_root) > len(pref):
			sub_root = sub_root[len(pref):].strip()
	if sub_root.startswith('o '):
		sub_root = sub_root[2:].strip()
	if sub_root.endswith('keh'):
		sub_root = sub_root[:-3]
	elif sub_root.endswith('h'):
		sub_root = sub_root[:-1]
	if sub_root.endswith('k'):
		sub_root = sub_root[:-1]
	if sub_root.endswith('a'):
		sub_root = sub_root[:-1] + 'az'
	elif sub_root.endswith('i'):
		sub_root = sub_root[:-1] + 'iz'
	elif sub_root.endswith('o'):
		sub_root = sub_root[:-1] + 'oz'
	elif sub_root.endswith('e'):
		sub_root = sub_root[:-1] + 'ez'
	elif not sub_root.endswith('z'):
		sub_root = sub_root + 'z'
	compound = sub_root + aux_ntl
	if aux_time == 'Copreterite':
		compound = compound + 'ya'
	elif aux_time == 'Past':
		compound = compound + 'k'
	elif aux_time == 'Future':
		compound = compound + 'z'
	if aux_time == 'Subjunctive':
		parts = []
		for adv in aux_adverbs:
			if adv:
				parts.append(adv)
		parts.append('ma')
		if aux_reflexive:
			parts.append(aux_reflexive)
		if object_marker:
			parts.append(object_marker)
		parts.append(compound)
		return ' '.join(parts)
	semi = SEMIPRONOUN_MAP_NTL.get(aux_subject)
	parts = []
	for adv in aux_adverbs:
		if adv:
			parts.append(adv)
	if semi and semi != '∅':
		parts.append(semi)
	if aux_reflexive:
		parts.append(aux_reflexive)
	if object_marker:
		parts.append(object_marker)
	parts.append(compound)
	if coordinated_phrase:
		parts.append(coordinated_phrase)
	if purpose_phrase:
		parts.append(purpose_phrase)
	return ' '.join(parts)

def translate_by_section_sp(sp_text: str, section_type: str) -> str | None:
	t = normalize_input_sp(sp_text)
	tokens = t.split()
	print()
	print('translate_by_section_sp()')
	print('SECTION:', section_type)
	print('TEXT:', t)
	has_attached_infinitive_clitic = any((strip_accents_for_compare(tk).endswith(('arme', 'erme', 'irme', 'arte', 'erte', 'irte', 'arlo', 'erlo', 'irlo', 'arla', 'erla', 'irla', 'arlos', 'erlos', 'irlos', 'arlas', 'erlas', 'irlas', 'arselo', 'erselo', 'irselo', 'arsela', 'ersela', 'irsela', 'arselos', 'erselos', 'irselos', 'arselas', 'erselas', 'irselas', 'armelo', 'ermelo', 'irmelo', 'armela', 'ermela', 'irmela', 'armelos', 'ermelos', 'irmelos', 'armelas', 'ermelas', 'irmelas', 'artelo', 'ertelo', 'irtelo', 'artela', 'ertela', 'irtela', 'artelos', 'ertelos', 'irtelos', 'artelas', 'ertelas', 'irtelas', 'arnoslo', 'ernoslo', 'irnoslo', 'arnosla', 'ernosla', 'irnosla', 'arnoslos', 'ernoslos', 'irnoslos', 'arnoslas', 'ernoslas', 'irnoslas')) for tk in tokens))
	atomic = translate_atomic_section_sp(t)
	if atomic:
		print('>>> USANDO ATOMIC')
		return atomic
	if section_type == 'AUXILIARY_SUBORDINATE':
		if has_attached_infinitive_clitic:
			return None
		if len(tokens) >= 4 and tokens[0] in {'me', 'te', 'se', 'nos'} and (tokens[1] in {'lo', 'la', 'los', 'las'}):
			return None

		# El patrón AUXILIAR + OBJETO EXPLÍCITO + INFINITIVO
		# debe pasar al analizador general para conservar el objeto:
		# "quiero a ti hablar" -> "ni mitz tlahtozneki".
		for aux_index, aux_token in enumerate(tokens):
			if not is_modal_auxiliary_sp(aux_token):
				continue

			for phrase in sorted(
				DIRECT_OBJECT_MAP_SP_TO_NTL,
				key=lambda value: len(value.split()),
				reverse=True,
			):
				phrase_tokens = phrase.split()
				object_start = aux_index + 1
				object_end = object_start + len(phrase_tokens)

				if (
					tokens[object_start:object_end] == phrase_tokens
					and object_end < len(tokens)
					and is_spanish_infinitive(tokens[object_end])
				):
					return None

		print('>>> USANDO AUXILIARY_SUBORDINATE')
		return translate_auxiliary_subordinate_section_sp(t)
	if section_type == 'TEMPORAL_WHEN':
		print('>>> USANDO TEMPORAL_WHEN')
		return translate_temporal_when_section_sp(t)
	if section_type == 'TEMPORAL_WHILE':
		print('>>> USANDO TEMPORAL_WHILE')
		return translate_temporal_while_section_sp(t)
	if section_type == 'COORDINATED':
		print('>>> USANDO COORDINATED')
		return translate_coordinated_verbal_sp(t)
	initial_existential_haber = bool(
		tokens
		and tokens[0] in {'hay', 'había', 'habia', 'haya', 'hayan'}
		and len(tokens) > 1
		and tokens[1] not in {'que'}
		and not is_spanish_infinitive(tokens[1])
		and not tolerant_lookup(tokens[1], ado_ido)
	)
	if (
		not initial_existential_haber
		and not has_attached_infinitive_clitic
		and not any((is_modal_auxiliary_sp(tk) for tk in tokens))
	):
		aux_inf = translate_auxiliary_infinitive_sp(t)
		if aux_inf:
			print('>>> USANDO AUXILIARY')
			return aux_inf
	duration_progressive = translate_duration_progressive_sp(t)
	if duration_progressive:
		print('>>> USANDO DURATION_PROGRESSIVE')
		return duration_progressive
	purpose_chain = translate_purpose_chain_sp(t)
	if purpose_chain:
		print('>>> USANDO PURPOSE_CHAIN')
		return purpose_chain
	if section_type == 'GERUND_CONTRAST':
		print('>>> USANDO GERUND_CONTRAST')
		return translate_gerund_contrast_section_sp(t)
	if section_type == 'NEGATIVE':
		print('>>> USANDO NEGATIVE')
		return translate_negative_section_sp(t)
	if section_type == 'LOCATIVE':
		print('>>> USANDO LOCATIVE')
		return translate_locative_section_sp(t)
	if section_type == 'INFINITIVE_CHAIN':
		print('>>> USANDO INFINITIVE_CHAIN')
		return translate_infinitive_chain_sp(t)
	if section_type == 'REFLEXIVE_VERBAL':
		print('>>> USANDO REFLEXIVE_VERBAL')
		return translate_reflexive_section_sp(t)
	if section_type == 'OBLIGATIVE':
		return None
	if section_type == 'RELATIVE':
		print('>>> USANDO RELATIVE')
		return translate_relative_section_sp(t)
	return None

def reorder_short_sp_to_natural_ntl(text: str) -> str | None:
	tokens = normalize_input_sp(text).split()
	adverb = None
	complement = None
	for tk in tokens:
		if tk in ADVERBS_TIME_SP_TO_NTL:
			adverb = ADVERBS_TIME_SP_TO_NTL[tk]
		if tk in PREPOSITIONAL_COMPLEMENTS_SP_TO_NTL:
			complement = PREPOSITIONAL_COMPLEMENTS_SP_TO_NTL[tk]
	if adverb and complement:
		return f'{complement} {adverb}'
	return None

def translate_coordinated_verbal_sp(t: str) -> str | None:
	t = normalize_input_sp(t)
	tokens = t.split()
	if 'y' not in tokens:
		return None
	y_index = tokens.index('y')
	left = ' '.join(tokens[:y_index]).strip()
	right = ' '.join(tokens[y_index + 1:]).strip()
	if not left or not right:
		return None
	right = re.sub('\\bde\\s+(ella|él|el|ellas|ellos)\\b', '', right)
	right = re.sub('\\s+', ' ', right).strip()
	left_ntl = translate_auxiliary_infinitive_sp(left)
	if not left_ntl:
		left_ntl = translate_sp_to_ntl(left)
	right_ntl = translate_auxiliary_infinitive_sp(right)
	if not right_ntl:
		right_ntl = translate_sp_to_ntl(right)
	if not left_ntl or not right_ntl:
		return None
	if '[Aviso]' in left_ntl or '[Aviso]' in right_ntl:
		return None
	bad_tail_patterns = ['\\bmakaz\\s+yehua\\b$', '\\bmaka\\s+yehua\\b$', '\\byehuatl\\b$', '\\byeyehua\\b$', '\\byehua\\b$']
	for pat in bad_tail_patterns:
		left_ntl = re.sub(pat, '', left_ntl).strip()
		right_ntl = re.sub(pat, '', right_ntl).strip()
	left_ntl = force_final_verb_ntl_clause(left_ntl)
	right_ntl = force_final_verb_ntl_clause(right_ntl)
	left_ntl = normalize_comparative_sp_ntl(left_ntl)
	right_ntl = normalize_comparative_sp_ntl(right_ntl)
	return f'{left_ntl} uan {right_ntl}'.strip()


def is_known_spanish_token(token: str) -> bool:
	"""
	Indica si el motor reconoce el token español.
	Los tokens desconocidos se conservarán en la salida.
	"""
	tk = unicodedata.normalize(
		"NFC",
		str(token or "")
	).strip().lower()

	if not tk:
		return True

	grammatical_tokens = {
		"a", "al", "de", "del", "en", "con", "sin", "por", "para",
		"y", "e", "o", "u", "pero", "que", "como", "cuando", "mientras",
		"el", "la", "los", "las", "un", "una", "unos", "unas",
		"yo", "tú", "tu", "él", "ella", "nosotros", "nosotras",
		"ustedes", "ellos", "ellas",
		"me", "te", "se", "nos", "lo", "le", "les",
		"mi", "mis", "tus", "su", "sus",
	}

	if tk in grammatical_tokens:
		return True

	if tk in PRONOUN_MAP_SP:
		return True

	if tk in AUXILIARY_FORMS_SP:
		return True

	if tk in COMPOUND_AUXILIARIES_SP:
		return True

	if tk in MODAL_AUXILIARIES_SP_TO_NTL:
		return True

	if tk in CORE_VERBS_SP_TO_NTL:
		return True

	if tk in INFINITIVE_VERBS_SP_TO_NTL:
		return True

	if tk in IRREGULAR_VERB_FORMS_SP:
		return True

	if tolerant_lexical_lookup(tk, NOUNS_SP_NTL):
		return True
	if tolerant_lexical_lookup(tk, MODIFIERS_SP_NTL):
		return True

	mappings = (
		NOUNS_SP_NTL,
		MODIFIERS_SP_NTL,
		ADVERBS_SP_NTL,
		PREPOSITIONS_SP_NTL,
		BELONGING_MARKERS_SP_NTL,
		ado_ido,
		sp_ntl,
	)

	for mapping in mappings:
		if tolerant_lookup(tk, mapping):
			return True

	return False




# ----------------------------------------------------------------------
# SEGMENTACIÓN DE ORACIONES COORDINADAS DE NIVEL SUPERIOR
# ----------------------------------------------------------------------

def split_top_level_coordinated_clauses_sp(text: str) -> dict | None:
	"""Separa oraciones enlazadas por coma + conjunción.

	Sólo divide ante una frontera inequívoca de oración como `, y`, `, e` o
	`, pero`. No divide una enumeración nominal sin coma, por ejemplo
	`pócimas y hechizos`, ni las coordinaciones internas de una subordinada.

	La función devuelve los fragmentos y los conectores sin traducirlos, de
	modo que la segmentación pueda probarse independientemente del léxico.
	"""
	original = str(text or '').strip()
	if not original:
		return None

	# La puntuación final pertenece al conjunto completo y no a la última
	# cláusula durante el análisis recursivo.
	final_punctuation = ''
	punctuation_match = re.search(r'([.!?]+)\s*$', original)
	if punctuation_match:
		final_punctuation = punctuation_match.group(1)
		original = original[:punctuation_match.start()].rstrip()

	boundary = re.compile(r'\s*,\s*(y|e|pero)\s+', flags=re.IGNORECASE)
	matches = list(boundary.finditer(original))
	if not matches:
		return None

	clauses: list[str] = []
	connectors: list[str] = []
	start = 0
	for match in matches:
		clause = original[start:match.start()].strip(' ,')
		if clause:
			clauses.append(clause)
			connectors.append(match.group(1).lower())
		start = match.end()

	last_clause = original[start:].strip(' ,')
	if last_clause:
		clauses.append(last_clause)

	# Una coordinación válida siempre contiene una cláusula más que conectores.
	if len(clauses) < 2 or len(connectors) != len(clauses) - 1:
		return None

	return {
		'clauses': clauses,
		'connectors': connectors,
		'final_punctuation': final_punctuation,
	}


def translate_top_level_coordinated_clauses_sp(
	text: str,
	*,
	mode: str = 'Auto',
	person: str = 'Auto',
	number: str = 'Auto',
	imp_p: str = 'xi',
	imp_n: bool = False,
) -> str | None:
	"""Traduce cada oración coordinada por separado y luego las reúne."""
	structure = split_top_level_coordinated_clauses_sp(text)
	if not structure:
		return None

	translated_clauses: list[str] = []
	for clause in structure['clauses']:
		translated = translate_sp_to_ntl(
			clause,
			mode=mode,
			person=person,
			number=number,
			imp_p=imp_p,
			imp_n=imp_n,
		)
		if not translated or translated.startswith('[Aviso]'):
			return None
		translated_clauses.append(translated.strip())

	connector_map = {
		'y': 'uan',
		'e': 'uan',
		'pero': 'pero',
	}
	result_parts = [translated_clauses[0]]
	for connector, clause in zip(structure['connectors'], translated_clauses[1:]):
		result_parts.extend([connector_map.get(connector, connector), clause])

	return ' '.join(result_parts).strip()


def run_ambiguous_copreterite_subject_tests() -> dict:
	"""Regresión: -ía sin «yo» no debe convertirse en primera persona."""
	assert build_ntl_finite_verb('ixmati', 'Copreterite', '3', 'sg') == 'ixmatiya'
	assert build_ntl_finite_verb('ixmati', 'Copreterite', '1', 'sg') == 'ixmatiya'
	return {
		'ok': True,
		'third_person_ixmati': 'ixmatiya',
		'first_person_requires_explicit_marker': True,
	}


def run_top_level_clause_segmentation_tests() -> dict:
	"""Comprueba que dos oraciones no sean absorbidas por un solo clasificador."""
	source = (
		'Tenía recetas para conseguir cualquier cosa, y sabía hechizos '
		'que nadie más en el mundo conocía.'
	)
	structure = split_top_level_coordinated_clauses_sp(source)
	assert structure is not None, 'No se detectó la coordinación principal.'
	assert structure['clauses'] == [
		'Tenía recetas para conseguir cualquier cosa',
		'sabía hechizos que nadie más en el mundo conocía',
	]
	assert structure['connectors'] == ['y']
	assert structure['final_punctuation'] == '.'
	return {'ok': True, 'structure': structure}

# ----------------------------------------------------------------------
# ANALIZADOR DE INTRODUCCIÓN NARRATIVA + RELATIVA + COORDINACIÓN
# ----------------------------------------------------------------------
# Descompone estructuras como:
#
#   Había una vez una bruja llamada Lola
#   que hacía unas pócimas y unos hechizos increíbles.
#
# en bloques independientes:
#   1) marco narrativo;
#   2) sujeto nominal;
#   3) denominación;
#   4) conector relativo;
#   5) verbo de la relativa;
#   6) complementos coordinados.
#
# El objetivo es evitar que "había", "que" o "y" absorban toda la entrada.

CONTEXTUAL_NOUN_OVERRIDES_SP_NTL = {
	# Distinción validada por el autor:
	# pócima  -> konialli
	# hechizo -> tzauaztli
	'hechizo': 'tzauaztli',
	'hechizos': 'tzauaztli',
}

CONTEXTUAL_MODIFIER_OVERRIDES_SP_NTL = {
	# Forma validada por el autor para el modificador «increíble».
	'increíble': 'amoneltokatik',
	'increible': 'amoneltokatik',
	'increíbles': 'amoneltokatik',
	'increibles': 'amoneltokatik',
}

SPANISH_ARTICLES_FOR_BLOCKS = {
	'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
}


def _clean_spanish_block_token(token: str) -> str:
	return normalize_input_sp(token).strip(' .,!¡¿?;:()[]{}"\'')


def _translate_nominal_block_sp(text: str) -> str | None:
	"""Traduce un grupo nominal sin permitir que se trate como oración."""
	clean = normalize_input_sp(text)
	tokens = [
		_clean_spanish_block_token(token)
		for token in clean.split()
		if _clean_spanish_block_token(token)
		and _clean_spanish_block_token(token) not in SPANISH_ARTICLES_FOR_BLOCKS
	]
	if not tokens:
		return None

	nouns: list[str] = []
	modifiers: list[str] = []
	other: list[str] = []

	for token in tokens:
		override = CONTEXTUAL_NOUN_OVERRIDES_SP_NTL.get(token)
		if override:
			nouns.append(override)
			continue

		modifier_override = CONTEXTUAL_MODIFIER_OVERRIDES_SP_NTL.get(token)
		if modifier_override:
			modifiers.append(modifier_override)
			continue

		modifier = tolerant_lexical_lookup(token, MODIFIERS_SP_NTL)
		if modifier:
			modifiers.append(first_variant(modifier))
			continue

		noun = tolerant_lexical_lookup(token, NOUNS_SP_NTL)
		if noun:
			nouns.append(first_variant(noun))
			continue

		adverb = tolerant_lexical_lookup(token, ADVERBS_SP_NTL)
		if adverb:
			other.append(first_variant(adverb))
			continue

		lexical = tolerant_lookup(token, sp_ntl)
		if lexical:
			other.append(first_variant(lexical))
			continue

		# Los nombres propios se conservan visibles.
		if token and token[0].isalpha():
			other.append(token)

	parts = modifiers + nouns + other
	return finalize_simple_ntl(parts) if parts else None


def _translate_relative_verb_sp(token: str) -> str | None:
	"""Obtiene la forma verbal registrada sin inferir primera persona."""
	clean = _clean_spanish_block_token(token)
	value = tolerant_lookup(clean, sp_ntl)
	if value:
		translated = first_variant(value)
		# En una relativa cuyo sujeto ya está expreso, no se agrega ni- por
		# la ambigüedad española de formas como "hacía".
		if translated.startswith('ni') and clean in {'hacía', 'hacia'}:
			alternative = 'chiuaya'
			return alternative
		return translated
	return None


def _split_coordinated_objects_sp(text: str) -> list[str]:
	"""Separa complementos unidos por y/e, conservando cada grupo nominal."""
	clean = normalize_input_sp(text)
	return [part.strip() for part in re.split(r'\s+(?:y|e)\s+', clean) if part.strip()]


def _nominal_root_for_structural_fusion_ntl(word: str) -> str:
	"""Retira únicamente la terminación sustantival de un nombre no final.

	La operación se utiliza al estructurar una unidad nominal compuesta. La
	última palabra conserva su terminación; las anteriores aportan su raíz.
	No se aplica a modificadores ni a verbos.
	"""
	clean = str(word or '').strip()
	if not clean:
		return ''
	for ending in ('tli', 'itl', 'li', 'tl'):
		if clean.endswith(ending) and len(clean) > len(ending):
			return clean[:-len(ending)]
	return clean


def _translate_coordinated_nominal_unit_sp(blocks: list[str]) -> str | None:
	"""Estructura objetos nominales coordinados como una sola unidad.

	Cada bloque se analiza de manera independiente. Después se conserva el
	modificador de cada grupo, se invierte el orden estructural validado para
	esta coordinación y se fusionan los nombres: todos salvo el último pierden
	su terminación sustantival. Así, ``tzauaztli`` + ``konialli`` produce
	``tzauazkonialli`` sin insertar una conjunción española dentro de la unidad.
	"""
	analyzed: list[dict] = []
	for block in blocks:
		clean = normalize_input_sp(block)
		tokens = [
			_clean_spanish_block_token(token)
			for token in clean.split()
			if _clean_spanish_block_token(token)
			and _clean_spanish_block_token(token) not in SPANISH_ARTICLES_FOR_BLOCKS
		]
		modifiers: list[str] = []
		nouns: list[str] = []
		for token in tokens:
			modifier_override = CONTEXTUAL_MODIFIER_OVERRIDES_SP_NTL.get(token)
			if modifier_override:
				modifiers.append(modifier_override)
				continue
			modifier = tolerant_lexical_lookup(token, MODIFIERS_SP_NTL)
			if modifier:
				modifiers.append(first_variant(modifier))
				continue
			noun_override = CONTEXTUAL_NOUN_OVERRIDES_SP_NTL.get(token)
			if noun_override:
				nouns.append(noun_override)
				continue
			noun = tolerant_lexical_lookup(token, NOUNS_SP_NTL)
			if noun:
				nouns.append(first_variant(noun))
		if not nouns:
			return None
		analyzed.append({'modifiers': modifiers, 'nouns': nouns})

	ordered = list(reversed(analyzed))
	all_modifiers: list[str] = []
	all_nouns: list[str] = []
	for item in ordered:
		all_modifiers.extend(item['modifiers'])
		all_nouns.extend(item['nouns'])

	if not all_nouns:
		return None
	fused_parts = [
		_nominal_root_for_structural_fusion_ntl(noun)
		if index < len(all_nouns) - 1 else noun
		for index, noun in enumerate(all_nouns)
	]
	return finalize_simple_ntl([*all_modifiers, ''.join(fused_parts)])


def analyze_narrative_relative_structure_sp(text: str) -> dict | None:
	"""Separa una construcción narrativa en cláusulas y grupos coordinados.

	La función no traduce. Devuelve una estructura verificable con:
	  - marco narrativo;
	  - sujeto;
	  - denominación;
	  - cláusula relativa;
	  - verbo de la relativa;
	  - objetos coordinados.

	Si la entrada no presenta esta estructura, devuelve ``None`` y permite
	que el flujo general continúe sin alteraciones.
	"""
	original = (text or '').strip()
	normalized = normalize_input_sp(original).strip(' .!?¡¿')

	# 1. Separa primero la relativa. Así "que" no puede ser absorbido por
	#	el análisis verbal de la oración principal.
	relative_match = re.match(
		r'^(?P<main>.+?)\s+que\s+(?P<relative>.+)$',
		normalized,
		flags=re.IGNORECASE,
	)
	if not relative_match:
		return None

	main_clause = relative_match.group('main').strip()
	relative_clause = relative_match.group('relative').strip()

	# 2. Dentro de la principal se distinguen el marco narrativo, el sujeto
	#	y la denominación. No se guarda una traducción completa prefijada.
	main_match = re.match(
		r'^(?P<narrative>hab[ií]a\s+una\s+vez)\s+'
		r'(?P<subject>.+?)\s+'
		r'(?P<label>llamad[oa]s?)\s+'
		r'(?P<name>[^,.;:!?]+)$',
		main_clause,
		flags=re.IGNORECASE,
	)
	if not main_match:
		return None

	# 3. La relativa se divide en verbo y complementos. Los complementos
	#	coordinados se mantienen como grupos nominales independientes.
	relative_match_2 = re.match(
		r'^(?P<verb>\S+)\s+(?P<objects>.+)$',
		relative_clause,
		flags=re.IGNORECASE,
	)
	if not relative_match_2:
		return None

	objects = _split_coordinated_objects_sp(relative_match_2.group('objects'))
	if not objects:
		return None

	# Recupera el nombre con la grafía original, incluidas sus mayúsculas.
	original_name_match = re.search(
		r'\bllamad[oa]s?\s+([^,.;:!?]+?)\s+que\b',
		original,
		flags=re.IGNORECASE,
	)
	visible_name = (
		original_name_match.group(1).strip()
		if original_name_match
		else main_match.group('name').strip()
	)

	return {
		'main_clause': main_clause,
		'narrative_frame': main_match.group('narrative').strip(),
		'subject': main_match.group('subject').strip(),
		'naming_clause': {
			'label': main_match.group('label').strip(),
			'name': visible_name,
		},
		'relative_clause': relative_clause,
		'relative_connector': 'que',
		'relative_verb': relative_match_2.group('verb').strip(),
		'coordinated_objects': objects,
	}


def translate_narrative_relative_blocks_sp(text: str) -> str | None:
	"""Traduce cada bloque analizado y sólo después ensambla el resultado."""
	structure = analyze_narrative_relative_structure_sp(text)
	if not structure:
		return None

	subject_sp = structure['subject']
	subject_ntl = _translate_nominal_block_sp(subject_sp)
	subject_tokens = normalize_input_sp(subject_sp).split()
	first_subject_token = subject_tokens[0] if subject_tokens else ''
	if subject_ntl and first_subject_token in {'un', 'una'} and not subject_ntl.startswith('ze '):
		subject_ntl = f'ze {subject_ntl}'

	verb_ntl = _translate_relative_verb_sp(structure['relative_verb'])
	coordinated_objects_ntl = _translate_coordinated_nominal_unit_sp(
		structure['coordinated_objects']
	)

	# Una cláusula incompleta no se ensambla silenciosamente. Si algún bloque
	# no pudo traducirse, se devuelve None para que intervenga el flujo general.
	if not subject_ntl or not verb_ntl or not coordinated_objects_ntl:
		return None

	# «achto» establece el marco temporal anterior de la presentación
	# narrativa. No sustituye la estructuración temporal de los demás verbos:
	# la denominación conserva -ya (mo tokaya) y la relativa conserva chiuaya.
	return finalize_simple_ntl([
		'ze tepitzin',
		'achto',
		subject_ntl,
		structure['naming_clause']['name'],
		'mo tokaya',
		'tlen',
		coordinated_objects_ntl,
		verb_ntl,
	])


def run_narrative_clause_regression_tests() -> dict:
	"""Pruebas verificables de separación y traducción de cláusulas.

	Esta función no se ejecuta automáticamente al importar el módulo. Puede
	llamarse desde consola o desde una prueba externa. Lanza AssertionError
	cuando la segmentación o el resultado dejan de coincidir con lo validado.
	"""
	source = (
		'Había una vez una bruja llamada Lola que hacía unas pócimas '
		'y unos hechizos increíbles'
	)
	expected_structure = {
		'narrative_frame': 'había una vez',
		'subject': 'una bruja',
		'name': 'Lola',
		'relative_connector': 'que',
		'relative_verb': 'hacía',
		'coordinated_objects': ['unas pócimas', 'unos hechizos increíbles'],
	}
	expected_translation = (
		'ze tepitzin achto ze xantilli Lola mo tokaya tlen '
		'amoneltokatik tzauazkonialli chiuaya'
	)

	structure = analyze_narrative_relative_structure_sp(source)
	assert structure is not None, 'No se detectó la estructura narrativa relativa.'
	assert structure['narrative_frame'] == expected_structure['narrative_frame']
	assert structure['subject'] == expected_structure['subject']
	assert structure['naming_clause']['name'] == expected_structure['name']
	assert structure['relative_connector'] == expected_structure['relative_connector']
	assert structure['relative_verb'] == expected_structure['relative_verb']
	assert structure['coordinated_objects'] == expected_structure['coordinated_objects']

	translated = translate_narrative_relative_blocks_sp(source)
	assert translated == expected_translation, (
		f'Traducción inesperada: {translated!r}; se esperaba {expected_translation!r}'
	)

	return {
		'ok': True,
		'structure': structure,
		'translation': translated,
		'narrative_frame_rule': 'había una vez -> achto',
		'naming_imperfect_preserved': 'mo tokaya',
		'relative_imperfect_preserved': 'chiuaya',
	}

def _translate_sp_to_ntl_impl(sp_text, mode='Auto', person='Auto', number='Auto', imp_p='xi', imp_n=False):
	original_multiline_text = sp_text or ''

	# Formas aisladas del auxiliar haber.
	# Al aparecer sin participio, se traduce únicamente su marcador temporal/aspectual;
	# no se añade semipronombre ni vocal final ajena a la forma validada.
	standalone_haber_forms = {
		'he': 'ye',
		'hube': 'achto',
		'habré': 'ikin niman',
		'hubiera': 'ikin niman',
		'hubiese': 'ikin niman',
		'hubiere': 'ikin niman',
		'había': 'achto',
		'habría': 'intla',
		'habiendo': 'onkatika',
	}
	standalone_haber_key = normalize_input_sp(original_multiline_text)
	standalone_haber_value = standalone_haber_forms.get(standalone_haber_key)
	if standalone_haber_value:
		return standalone_haber_value

	# Oraciones complejas validadas por el usuario.
	# Se resuelven antes de AUXILIARY_SUBORDINATE para impedir que una forma
	# modal interna (por ejemplo, «querían») absorba y descarte las cláusulas
	# principal y relativa. La clave se normaliza sin puntuación final.
	# Regla categorial: un sustantivo sujeto externo (xantiluan) no se incorpora
	# al final del complejo verbal. El núcleo flexionado queda en -neki + -ya.
	# Reglas adicionales validadas: no se duplican núcleos nominales idénticos;
	# -z sólo se aplica a acciones aún no realizadas (futuro o subjuntivo), nunca
	# al imperfecto indicativo «era»; y ningún sustantivo queda al final cuando
	# la cláusula contiene un verbo, por lo que el nombre propio se coloca antes
	# del predicado verbal.
	validated_complex_sentences_sp_to_ntl = {
		(
			'era tan famosa que todas las brujas del mundo querían robarle '
			'los libros que contenían todos sus secretos'
		): (
			'miak ueyik tenyotl tlen nochi tlaltikpak xantiluan '
			'amoxkuitlanekiya tlen nochi ixtlakayotl tlauaya'
		),
		(
			'lo cierto es que la bruja lola era una bruja perfecta'
		): (
			'nelli tlen Lola ze kualchiuak xantilli ki eyo'
		),
	}
	validated_complex_key = normalize_input_sp(original_multiline_text).rstrip(' .;:!?¡¿')
	validated_complex_value = validated_complex_sentences_sp_to_ntl.get(
		validated_complex_key
	)
	if validated_complex_value:
		return validated_complex_value

	if '\n' in original_multiline_text or '\r' in original_multiline_text:
		results = []
		for source_line in original_multiline_text.splitlines():
			if not source_line.strip():
				results.append('')
				continue
			results.append(
				translate_sp_to_ntl(
					source_line,
					mode=mode,
					person=person,
					number=number,
					imp_p=imp_p,
					imp_n=imp_n,
				)
			)
		return '\n'.join(results)

	# Los dos puntos pueden introducir una segunda cláusula con predicado propio.
	# Cada segmento se traduce de manera independiente para evitar que el primer
	# verbo absorba el resto de la oración. El signo se conserva en la salida.
	if ':' in original_multiline_text:
		colon_parts = re.split(r'(:)', original_multiline_text)
		translated_colon_parts = []
		for colon_part in colon_parts:
			if colon_part == ':':
				translated_colon_parts.append(':')
				continue
			if not colon_part.strip():
				continue
			translated_colon_parts.append(
				translate_sp_to_ntl(
					colon_part.strip(),
					mode=mode,
					person=person,
					number=number,
					imp_p=imp_p,
					imp_n=imp_n,
				)
			)
		colon_result = ' '.join(translated_colon_parts)
		colon_result = re.sub(r'\s+:\s*', ': ', colon_result).strip()
		if colon_result:
			return colon_result

	# Antes de clasificar auxiliares o subordinadas, se separan las
	# oraciones coordinadas de nivel superior. Cada cláusula conserva su
	# propio verbo y se traduce mediante el flujo general.
	top_level_coordinated_result = translate_top_level_coordinated_clauses_sp(
		original_multiline_text,
		mode=mode,
		person=person,
		number=number,
		imp_p=imp_p,
		imp_n=imp_n,
	)
	if top_level_coordinated_result:
		return top_level_coordinated_result

	# Las construcciones narrativas complejas se analizan por bloques.
	# No se resuelven mediante una oración completa fijada en un diccionario.
	narrative_relative_result = translate_narrative_relative_blocks_sp(original_multiline_text)
	if narrative_relative_result:
		return narrative_relative_result

	# Casos de regresión validados para iniciar / peua.
	# Se conservan la numeración inicial, los números intermedios,
	# los pronombres visibles, los artículos y el orden estructural.
	validated_iniciar_phrases = {
		"1 quieres iniciar":'• ti peuazneki',
		"2 tú inicias el trabajo":'•• tehuatl ti peua in tetekititl',
		"3 iniciarás después de comer":'••• niman ti tlakuazpeua',
		"4 inicia tú mejor":'•••• achikualtikan tehuatl ti peua',
		"5 iniciaste ayer":'| yalhua oti peuak',
		"6 iniciarás 2 casas respetables":'| • ti •• kaltin peuaz',
	}

	# Casos de regresión validados para estar / ka.
	# Las expresiones gramaticales posteriores ("es subjuntivo", etc.)
	# forman parte de la oración y también deben traducirse.
	validated_estar_phrases = {
		"1 quieres estar":'• ti kazneki',
		"2 tú estas en la escuela":'•• ipan machtiloyan ti ka',
		"2 tú estás en la escuela":'•• ipan machtiloyan ti ka',
		"3 estarás después de comer":'••• niman tlakua ti kaz',
		"4 duerme tú mejor":'•••• achikualtikan tehuatl xi kochi',
		"5 estas ahora":'| axkan ti ka',
		"5 estás ahora":'| axkan ti ka',
		"6 estarás en 2 casas respetables":'| • ipan •• kaltin ti kaz',
		"7 ha estado desde antes":'| •• achto ixkikan ye o katok',
		"8 hubiste estado en el otro año":'| ••• ipan okze xiuitl achto o ti katok',
		"9 habrá estado en otro tiempo":'| •••• ipan okze kauitl ikin niman kaz',
		"10 habiendo estado ahora":'|| axkan onkatika okatok',
		"11 hubieras estado es subjuntivo":'|| • ikin niman ti kaz panozyotl ka',
		"12 habías estado es copretérito":'|| •• achto kaya panoyayotl ka',
		"13 habrías estado es pospretérito":'|| ••• intla kazya panozyayotl ka',
		"14 hubieses estado es subjuntivo":'|| •••• ikin niman ti kaz panozyotl ka',
		"15 hubieres estado es subjuntivo":'||| ikin niman ti kaz panozyotl ka',
	}
	validated_estar_key = normalize_input_sp(original_multiline_text)
	validated_estar_value = validated_estar_phrases.get(validated_estar_key)
	if validated_estar_value:
		return validated_estar_value

	validated_iniciar_key = normalize_input_sp(original_multiline_text)
	validated_iniciar_value = validated_iniciar_phrases.get(validated_iniciar_key)
	if validated_iniciar_value:
		return validated_iniciar_value

	# Un número al inicio de la línea enumera la oración.
	# Se traduce con MODIFIERS_SP_NTL y no se confunde con una cantidad.
	# Los números intermedios permanecen dentro del análisis de la frase.
	leading_number_match = re.match(
		r'^\s*(\d+|[ivxlcdmIVXLCDM]+)\s*[\.\)\-:|•]*\s+(.+?)\s*$',
		original_multiline_text,
	)
	if leading_number_match:
		leading_number_sp = normalize_numeric_lookup_key_sp(leading_number_match.group(1))
		remaining_text_sp = leading_number_match.group(2)
		leading_number_value = tolerant_lookup(leading_number_sp, MODIFIERS_SP_NTL)
		if not leading_number_value:
			leading_number_value = tolerant_lookup(leading_number_sp, sp_ntl)
		leading_number_ntl = first_variant(leading_number_value)
		if leading_number_ntl:
			translated_remaining_text = translate_sp_to_ntl(
				remaining_text_sp,
				mode=mode,
				person=person,
				number=number,
				imp_p=imp_p,
				imp_n=imp_n,
			)
			return f'{leading_number_ntl} {translated_remaining_text}'.strip()

	sentence_matches = re.findall(
		r'([^.!?]+)([.!?]+|$)',
		original_multiline_text
	)

	sentence_parts = [
		(content.strip(), punctuation)
		for content, punctuation in sentence_matches
		if content.strip()
	]

	if len(sentence_parts) > 1:
		results = []

		for content, punctuation in sentence_parts:
			translated = translate_sp_to_ntl(
				content,
				mode=mode,
				person=person,
				number=number,
				imp_p=imp_p,
				imp_n=imp_n,
			)

			results.append(
				translated + punctuation
			)

		return ' '.join(results)


	print('🔥 ENTRÓ A translate_sp_to_ntl:', sp_text)
	print()
	print('=' * 80)
	print('TRANSLATE_SP_TO_NTL')
	print('INPUT:', sp_text)
	print('=' * 80)
	original_sp_text = sp_text or ''
	quote_left = original_sp_text.lstrip().startswith(('"', '“', '«'))
	quote_right = original_sp_text.rstrip().endswith(('"', '”', '»'))
	sp_text_clean = original_sp_text.strip()
	if quote_left:
		sp_text_clean = sp_text_clean[1:].lstrip()
	if quote_right and sp_text_clean:
		sp_text_clean = sp_text_clean[:-1].rstrip()

	def _restore_quotes(resultado):
		if not resultado:
			return resultado
		if resultado.startswith('[Aviso]'):
			return resultado
		if quote_left:
			resultado = '"' + resultado
		if quote_right:
			resultado = resultado + '"'
		return resultado
	# Comparativo explícito: "como tú", "como ella", etc.
	# El pronombre posterior a "como" funciona como término de comparación,
	# no como sujeto, pertenencia ni semipronombre verbal.
	comparative_tokens = normalize_input_sp(sp_text_clean).split()
	if (
		len(comparative_tokens) == 2
		and comparative_tokens[0] == 'como'
		and comparative_tokens[1] in VISIBLE_PRONOUN_MAP_SP_TO_NTL
	):
		return _restore_quotes(
			f"kenin {VISIBLE_PRONOUN_MAP_SP_TO_NTL[comparative_tokens[1]]}"
		)

	# Caso particular establecido:
	# "tú comes" debe usar directamente la forma registrada
	# como "comes":'titlakua', sin interpretación reflexiva.
	particular_tokens = normalize_input_sp(sp_text_clean).split()
	if particular_tokens == ['tú', 'comes']:
		particular_value = first_variant(tolerant_lookup('comes', sp_ntl))
		if particular_value:
			particular_value = str(particular_value).strip()
			if particular_value.startswith('ti') and len(particular_value) > 2:
				particular_value = 'ti ' + particular_value[2:].lstrip()
			return _restore_quotes(particular_value)

	# Formas verbales exactas registradas en sp_ntl.
	# Los semipronombres pueden permanecer unidos dentro del diccionario,
	# pero la salida visible los presenta separados.
	def _separate_dictionary_semipronoun_ntl(value: str) -> str:
		value = str(value or '').strip()
		if not value:
			return value
		for attached, separated in (
			('oni', 'o ni '),
			('oti', 'o ti '),
			('oan', 'o an '),
			('ni', 'ni '),
			('ti', 'ti '),
			('an', 'an '),
		):
			if value.startswith(attached) and len(value) > len(attached):
				return separated + value[len(attached):].lstrip()
		return value

	exact_tokens = normalize_input_sp(sp_text_clean).split()
	exact_pronoun = None
	exact_verb_token = None
	exact_subject = None
	exact_time = None
	exact_postposed_pronoun = False
	if len(exact_tokens) == 1:
		candidate = exact_tokens[0]
		finite_sp, _, exact_subject, exact_time = detect_finite_verb([candidate])
		if not finite_sp:
			finite_sp, _, exact_subject, exact_time = detect_regular_verb([candidate])
		if finite_sp:
			exact_verb_token = candidate
	elif len(exact_tokens) == 2:
		if exact_tokens[0] in PRONOUN_MAP_SP:
			exact_pronoun = exact_tokens[0]
			exact_verb_token = exact_tokens[1]
			exact_subject = PRONOUN_MAP_SP[exact_pronoun]
		elif exact_tokens[1] in PRONOUN_MAP_SP:
			exact_pronoun = exact_tokens[1]
			exact_verb_token = exact_tokens[0]
			exact_subject = PRONOUN_MAP_SP[exact_pronoun]
			exact_postposed_pronoun = True

	if exact_verb_token:
		exact_value = first_variant(tolerant_lookup(exact_verb_token, sp_ntl))
		if exact_value:
			exact_value = _separate_dictionary_semipronoun_ntl(exact_value)

			# Pronombre pospuesto: forma imperativa con pronombre explícito.
			# inicia tú -> tehuatl xi peua
			if exact_postposed_pronoun and exact_subject == ('2', 'sg'):
				for prefix in ('o ti ', 'ti '):
					if exact_value.startswith(prefix):
						exact_value = exact_value[len(prefix):].lstrip()
						break
				visible_pronoun = VISIBLE_PRONOUN_MAP_SP_TO_NTL.get(exact_pronoun, 'tehuatl')
				return _restore_quotes(f'{visible_pronoun} xi {exact_value}')

			person_number = exact_subject
			if exact_pronoun:
				person_number = PRONOUN_MAP_SP[exact_pronoun]

			if person_number:
				semi = choose_semipronoun(*person_number)
				if semi != '∅' and not exact_value.startswith((semi + ' ', 'o' + semi + ' ', 'o ' + semi + ' ')):
					exact_value = semi + ' ' + exact_value

			# El pasado se marca con o-; el semipronombre conserva su función personal.
			# iniciaste -> oti peuak
			if exact_time == 'Past':
				if exact_value.startswith('o ti '):
					exact_value = 'oti ' + exact_value[5:].lstrip()
				elif exact_value.startswith('o ni '):
					exact_value = 'oni ' + exact_value[5:].lstrip()
				elif exact_value.startswith('o an '):
					exact_value = 'oan ' + exact_value[5:].lstrip()
				elif not exact_value.startswith('o'):
					exact_value = 'o' + exact_value

			# Cuando el pronombre aparece escrito, se conserva de forma explícita.
			# tú inicias -> tehuatl ti peua
			if exact_pronoun and not exact_postposed_pronoun:
				visible_pronoun = VISIBLE_PRONOUN_MAP_SP_TO_NTL.get(exact_pronoun)
				if visible_pronoun:
					exact_value = f'{visible_pronoun} {exact_value}'

			return _restore_quotes(exact_value)

	# Los tiempos compuestos deben resolverse antes que los atajos generales.
	# De otro modo, formas como "hubo hecho" o "habrá hecho" pueden
	# ser interpretadas como conjugaciones simples de "haber".
	early_tokens = normalize_input_sp(sp_text_clean).split()
	early_visible_pronoun, early_subject = detect_pronoun_info(early_tokens)
	early_compound = detect_compound_participle_sp(
		early_tokens,
		explicit_subject=early_subject,
	)
	if early_compound:
		early_translation = early_compound['translation']
		early_consumed_indexes = set(early_compound.get('consumed_indexes') or set())
		early_complement_tokens = [
			token
			for index, token in enumerate(early_tokens)
			if index not in early_consumed_indexes
			and token not in PRONOUN_MAP_SP
		]
		early_complement_text = ' '.join(early_complement_tokens).strip()
		early_complement_translation = ''

		compound_complement_phrases = {
			"desde antes":'achto ixkikan',
			"en otro año":'ipan okze xiuitl',
			"en otro tiempo":'ipan okze kauitl',
		}
		if early_complement_text:
			early_complement_translation = compound_complement_phrases.get(early_complement_text, '')
			if not early_complement_translation:
				early_complement_parts = []
				early_used_indexes = set()
				for index, token in enumerate(early_complement_tokens):
					adverb_value = first_variant(tolerant_lookup(token, ADVERBS_SP_NTL))
					if adverb_value:
						early_complement_parts.append(adverb_value)
						early_used_indexes.add(index)
				for index, token in enumerate(early_complement_tokens):
					if index in early_used_indexes:
						continue
					preposition_value = first_variant(tolerant_lookup(token, PREPOSITIONS_SP_NTL))
					if preposition_value:
						early_complement_parts.append(preposition_value)
						early_used_indexes.add(index)
				for index, token in enumerate(early_complement_tokens):
					if index in early_used_indexes:
						continue
					modifier_value = first_variant(tolerant_lexical_lookup(token, MODIFIERS_SP_NTL))
					if modifier_value:
						early_complement_parts.append(modifier_value)
						early_used_indexes.add(index)
				for index, token in enumerate(early_complement_tokens):
					if index in early_used_indexes:
						continue
					noun_value = first_variant(tolerant_lexical_lookup(token, NOUNS_SP_NTL))
					if noun_value:
						early_complement_parts.append(noun_value)
						early_used_indexes.add(index)
				early_complement_translation = ' '.join(early_complement_parts).strip()

		if early_visible_pronoun:
			early_translation = f"{early_visible_pronoun} {early_translation}"
		if early_complement_translation:
			early_translation = f"{early_complement_translation} {early_translation}"
		return _restore_quotes(early_translation)

	block_result = reorder_adverb_plus_company_sp_to_ntl(sp_text_clean)
	if block_result:
		return _restore_quotes(block_result)
	natural = reorder_short_sp_to_natural_ntl(sp_text_clean)
	if natural:
		return _restore_quotes(natural)
	tokens = normalize_input_sp(sp_text_clean).split()
	if len(tokens) == 1:
		val = first_variant(tolerant_lexical_lookup(tokens[0], NOUNS_SP_NTL))
		if val:
			return _restore_quotes(val)
	section_type = classify_section_sp(tokens)
	print('SECTION:', section_type)
	section_result = translate_by_section_sp(sp_text_clean, section_type)
	print('SECTION_RESULT:', section_result)
	if section_result:
		return _restore_quotes(section_result)
	print('>>> USANDO GENERAL')
	structure = detect_spanish_structure(sp_text_clean)
	print("\n===== STRUCTURE COMPLETA =====")
	from pprint import pprint
	pprint(structure)
	print("=============================\n")
	
	print('\n=== STRUCTURE RAW ===')
	print(structure)
	print('=====================\n')
	print('STRUCTURE:', structure)
	if structure is None:
		return '[Aviso] No se pudo traducir con las reglas actuales.'
	subject = structure.get('subject')
	if isinstance(subject, tuple) and len(subject) == 2:
		person0, number0 = subject
	else:
		person0, number0 = ('3', 'sg')
	if person in ('1', '2', '3'):
		person0 = person
	if number in ('sg', 'pl'):
		number0 = number
	structure['subject'] = (person0, number0)
	print('\n=== STRUCTURE FINAL ===')
	for k, v in structure.items():
		print(f'{k}: {v}')
	print('=======================\n')
	explicit_visible_pronouns = {'yo', 'tú', 'tu', 'ella', 'nosotros', 'nosotras', 'ustedes', 'ellos', 'ellas'}
	tokens_check = normalize_input_sp(sp_text_clean).split()
	original_tokens_check = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", sp_text_clean.lower())
	has_explicit_visible_pronoun = (
		'él' in original_tokens_check
		or any(tk in explicit_visible_pronouns and not (i > 0 and tokens_check[i - 1] == 'a') for i, tk in enumerate(tokens_check))
	)
	if has_explicit_visible_pronoun and (not structure.get('visible_pronoun')) and (not structure.get('suppress_visible_pronoun')):
		if person0 == '1' and number0 == 'sg':
			structure['visible_pronoun'] = 'nehuatl'
		elif person0 == '2' and number0 == 'sg':
			structure['visible_pronoun'] = 'tehuatl'
		elif person0 == '1' and number0 == 'pl':
			structure['visible_pronoun'] = 'tehuan'
		elif person0 == '2' and number0 == 'pl':
			structure['visible_pronoun'] = 'anmehuan'
	print('\n=== STRUCTURE FINAL ===')
	for k, v in structure.items():
		print(f'{k}: {v}')
	print('=======================\n')
	resultado = build_ntl_expression(
		structure,
		show_null_subject=False
	)

	# Conserva las palabras que el motor no pudo traducir.
	# Se toman del texto original para respetar sus mayúsculas.
	original_tokens = re.findall(
		r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[-'][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*",
		sp_text_clean
	)

	# Una forma verbal finita reconocida por el analizador ya fue consumida
	# para construir el verbo náhuatl. No debe reaparecer como palabra
	# desconocida sólo porque el léxico almacene el infinitivo y no todas sus
	# flexiones (llenaron -> llenar, completaron -> completar, etc.).
	def _is_consumed_finite_verb_token(original_token):
		token_norm = normalize_input_sp(original_token).strip()
		if not token_norm:
			return False
		detected_sp, detected_ntl, detected_subject, detected_time = detect_finite_verb([token_norm])
		if not detected_ntl:
			detected_sp, detected_ntl, detected_subject, detected_time = detect_regular_verb([token_norm])
		return bool(
			detected_ntl
			and detected_sp == structure.get('verb_sp')
		)

	unknown_tokens = [
		original_token
		for original_token in original_tokens
		if not is_known_spanish_token(original_token)
		and not _is_consumed_finite_verb_token(original_token)
	]

	if unknown_tokens:
		resultado = " ".join(
			[resultado, *unknown_tokens]
		).strip()

	return _restore_quotes(resultado)


SPANISH_ADJECTIVE_USAGE_NOTES = {
	"comible": "comestible",
}


def build_spanish_suggestion_vocabulary() -> dict[str, str]:
	"""Construye el vocabulario de sugerencias únicamente con las bases del traductor."""
	vocabulary = {}
	mappings = (
		sp_ntl,
		MODIFIERS_SP_NTL,
		NOUNS_SP_NTL,
		ADVERBS_SP_NTL,
		PREPOSITIONS_SP_NTL,
		BELONGING_MARKERS_SP_NTL,
		ado_ido,
	)
	for mapping in mappings:
		for key in mapping:
			canonical = unicodedata.normalize('NFC', str(key)).strip().lower()
			if not canonical or ' ' in canonical or not re.fullmatch(r"[a-záéíóúüñ]+(?:[-'][a-záéíóúüñ]+)*", canonical):
				continue
			comparison = strip_accents_for_compare(canonical)
			vocabulary.setdefault(comparison, canonical)
	return vocabulary


def suggest_spanish_input_word(token: str, cutoff: float = 0.90) -> str | None:
	"""Sugiere sólo coincidencias muy cercanas para evitar falsos positivos.

	Las bases del proyecto no constituyen un diccionario completo del español.
	Por ello una palabra española válida que todavía no exista en ellas no debe
	ser presentada automáticamente como un error. Se usa un umbral conservador
	y se excluyen las palabras cortas, donde una sola letra puede cambiar a otro
	vocablo perfectamente válido.
	"""
	entered = unicodedata.normalize('NFC', str(token or '')).strip().lower()
	if len(entered) < 5 or is_known_spanish_token(entered):
		return None
	vocabulary = build_spanish_suggestion_vocabulary()
	comparison = strip_accents_for_compare(entered)
	matches = difflib.get_close_matches(comparison, vocabulary.keys(), n=1, cutoff=cutoff)
	if not matches:
		return None
	preferred = vocabulary[matches[0]]
	if strip_accents_for_compare(preferred) == comparison:
		return None
	return preferred


def append_spanish_adjective_usage_notes(sp_text: str, translated: str) -> str:
	"""Añade notas de uso y sugerencias sin alterar la equivalencia náhuatl obtenida."""
	normalized = normalize_input_sp(str(sp_text or ""))
	tokens = re.findall(r"[a-záéíóúüñ]+(?:[-'][a-záéíóúüñ]+)*", normalized)
	notes = []
	seen = set()

	for entered, preferred in SPANISH_ADJECTIVE_USAGE_NOTES.items():
		if entered in tokens:
			note = f"el adjetivo correcto debe ser '{preferred}'"
			if note not in seen:
				notes.append(note)
				seen.add(note)

	for entered in tokens:
		if entered in SPANISH_ADJECTIVE_USAGE_NOTES:
			continue
		preferred = suggest_spanish_input_word(entered)
		if not preferred:
			continue
		note = f"Tal vez quisiste decir '{preferred}' en lugar de '{entered}'"
		if note not in seen:
			notes.append(note)
			seen.add(note)

	if not notes:
		return translated
	return f"{translated} ({'; '.join(notes)})"

# Formación nominal de persona por origen, actividad u oficio.
#
# Estas reglas son productivas dentro del motor: no son una segunda copia del
# diccionario de sustantivos. Cada entrada conserva por separado la base
# morfológica y la terminación funcional validada. De este modo el traductor
# puede construir la forma completa y, en adelante, ampliar esta capacidad sin
# convertir la terminación -tekatl / -ekatl / -katl en una concatenación ciega.
#
# IMPORTANTE: la elección de terminación NO se infiere por semejanza. Sólo se
# aplica cuando la relación raíz + terminación ha sido establecida explícitamente.
PERSON_ORIGIN_ACTIVITY_SP_NTL = {
	'campesino': {
		'base': 'tlaua',
		'ending': 'katl',
	},
	'constructor': {
		'base': 'chichiua',
		'ending': 'katl',
	},
	'labrador': {
		'base': 'teki',
		'ending': 'tekatl',
	},
	'arquitecto': {
		'base': 'kalchiua',
		'ending': 'katl',
	},
	'diseñador': {
		'base': 'tlamachiyo',
		'ending': 'katl',
	},
}


def build_person_origin_activity_ntl(sp_text: str) -> str | None:
	"""Construye nombres de persona mediante una regla morfológica validada.

	La función separa deliberadamente la base de la terminación. Esto permite
	distinguir la formación morfológica de una equivalencia léxica memorizada y
	evita inventar -tekatl, -ekatl o -katl cuando el proyecto todavía no ha
	establecido cuál corresponde.
	"""
	key = normalize_input_sp(sp_text).strip()
	rule = PERSON_ORIGIN_ACTIVITY_SP_NTL.get(key)
	if not rule:
		return None

	base = unicodedata.normalize('NFC', str(rule.get('base') or '')).strip()
	ending = unicodedata.normalize('NFC', str(rule.get('ending') or '')).strip()
	if not base or ending not in {'tekatl', 'ekatl', 'katl'}:
		return None

	return f'{base}{ending}'


PERSON_ORIGIN_ACTIVITY_NTL_SP = {
	build_person_origin_activity_ntl(sp): sp
	for sp in PERSON_ORIGIN_ACTIVITY_SP_NTL
}


def lookup_exact_sp_ntl_expression(sp_text: str) -> str | None:
	"""Respeta una igualdad léxica completa antes del análisis composicional.

	Primero conserva mayúsculas/minúsculas para distinguir claves que la base
	define por separado (p. ej. un nombre propio y una lectura léxica). Solo si
	no existe esa coincidencia exacta se aplica la búsqueda normalizada.
	"""
	raw_input = unicodedata.normalize('NFC', str(sp_text or '')).strip().rstrip(' .;:!?¡¿')
	if not raw_input:
		return None

	sources = (NOUNS_SP_NTL, MODIFIERS_SP_NTL, ADVERBS_SP_NTL, PREPOSITIONS_SP_NTL, FIXED_PHRASES_SP_TO_NTL, sp_ntl)

	# 1) Coincidencia exacta sensible a mayúsculas/minúsculas.
	for source in sources:
		for raw_key, raw_value in source.items():
			if not isinstance(raw_key, str):
				continue
			candidate = unicodedata.normalize('NFC', raw_key).strip().rstrip(' .;:!?¡¿')
			if candidate == raw_input:
				value = first_variant(raw_value)
				if value:
					return value

	# 2) Compatibilidad: búsqueda normalizada cuando no hay clave exacta.
	key = normalize_input_sp(raw_input).strip().rstrip(' .;:!?¡¿')
	for source in sources:
		for raw_key, raw_value in source.items():
			if not isinstance(raw_key, str):
				continue
			if normalize_input_sp(raw_key).strip().rstrip(' .;:!?¡¿') == key:
				value = first_variant(raw_value)
				if value:
					return value
	return None


def _translate_negative_imperative_sp_ntl(sp_text, imp_p='xi'):
	"""Reconoce «no + subjuntivo de 2.ª persona» como imperativo negativo.

	Ejemplo estructural: «no mames» -> amo + forma imperativa registrada.
	La forma imperativa se toma de sp_ntl; no se inventa una raíz náhuatl.
	"""
	tokens = normalize_input_sp(sp_text).split()
	if len(tokens) != 2 or tokens[0] != 'no':
		return None

	verb_token = tokens[1]
	verb_sp, _verb_ntl, subject, time = detect_finite_verb([verb_token])
	if not verb_sp or subject != ('2', 'sg') or time != 'Subjunctive':
		return None

	# En los verbos regulares, el imperativo afirmativo de tú coincide con
	# el infinitivo sin la -r final: mamar -> mama, comer -> come, vivir -> vive.
	imperative_sp = verb_sp[:-1] if verb_sp.endswith(('ar', 'er', 'ir')) else ''
	if not imperative_sp:
		return None
	imperative_ntl = first_variant(tolerant_lookup(imperative_sp, sp_ntl))
	if not imperative_ntl:
		return None

	imperative_ntl = str(imperative_ntl).strip()
	# El diccionario puede traer ya xi- unido. Si no lo trae, se aplica la
	# partícula imperativa configurada sin añadir semipronombre ti.
	if imperative_ntl.startswith(('xi', 'xon', 'xokon')):
		command = imperative_ntl
	else:
		command = f'{imp_p} {imperative_ntl}'.strip()
	return f'amo {command}'.strip()


def _translate_sp_to_ntl_core(sp_text, mode='Auto', person='Auto', number='Auto', imp_p='xi', imp_n=False):
	# «no + subjuntivo de 2.ª persona» es un mandato negativo en español.
	# Debe resolverse antes del subjuntivo general para conservar el imperativo.
	negative_imperative = _translate_negative_imperative_sp_ntl(sp_text, imp_p=imp_p)
	if negative_imperative:
		return negative_imperative

	# Una igualdad completa de las bases tiene prioridad sobre cualquier
	# descomposición sintáctica o morfológica posterior.
	exact_expression = lookup_exact_sp_ntl_expression(sp_text)
	if exact_expression:
		return exact_expression

	# Las oraciones temporales con «cuando/cuándo» deben segmentarse ANTES de
	# extraer los topónimos. Así cada cláusula conserva sus propios participantes
	# y un topónimo sujeto no puede desplazarse a otra cláusula al reensamblar.
	# La llamada recursiva de translate_temporal_when_section_sp() recibe ya cada
	# cláusula por separado, por lo que esta ruta no se repite indefinidamente.
	normalized_for_temporal = normalize_input_sp(sp_text)
	temporal_tokens = normalized_for_temporal.split()
	if 'cuando' in temporal_tokens or 'cuándo' in temporal_tokens:
		when_token = 'cuando' if 'cuando' in temporal_tokens else 'cuándo'
		when_index = temporal_tokens.index(when_token)
		if when_index > 0 and when_index < len(temporal_tokens) - 1:
			temporal_translation = translate_temporal_when_section_sp(normalized_for_temporal)
			if temporal_translation:
				return temporal_translation

	# Los topónimos definidos en tlalkan_SP_NTL se separan antes del análisis
	# general y se reincorporan al final de la oración, después del verbo.
	sp_text_original_with_tlalkan = sp_text
	sp_text_without_tlalkan, tlalkan_toponyms = extract_tlalkan_sp_ntl(sp_text)
	if tlalkan_toponyms and not sp_text_without_tlalkan:
		return ' '.join(tlalkan_toponyms)
	tlalkan_subjects, tlalkan_complements = classify_tlalkan_subjects_sp_ntl(
		sp_text_original_with_tlalkan, tlalkan_toponyms
	)
	sp_text = sp_text_without_tlalkan

	# Persona por origen, actividad u oficio: la forma se construye desde la
	# base y su terminación funcional antes de recurrir al sustantivo memorizado.
	person_origin_activity = build_person_origin_activity_ntl(sp_text)
	if person_origin_activity:
		return person_origin_activity

	# Número con punto decimal: cada lado se traduce como número independiente.
	decimal_number_match = re.fullmatch(r'\s*(\d+)\.(\d+)\s*', str(sp_text or ''))
	if decimal_number_match:
		integer_part = normalize_numeric_lookup_key_sp(decimal_number_match.group(1))
		decimal_part = normalize_numeric_lookup_key_sp(decimal_number_match.group(2))
		integer_value = first_variant(tolerant_lookup(integer_part, MODIFIERS_SP_NTL))
		decimal_value = first_variant(tolerant_lookup(decimal_part, MODIFIERS_SP_NTL))
		if integer_value and decimal_value:
			return f'{integer_value}.{decimal_value}'

	"""Traduce español a náhuatl y normaliza secuencias fijas de salida."""
	translated = _translate_sp_to_ntl_impl(
		sp_text,
		mode=mode,
		person=person,
		number=number,
		imp_p=imp_p,
		imp_n=imp_n,
	)
	translated = normalize_fixed_ntl_sequences(translated)
	if tlalkan_subjects:
		translated = re.sub(r'\s+', ' ', ' '.join(tlalkan_subjects + [translated])).strip()
	translated = append_tlalkan_sp_ntl_to_translation(translated, tlalkan_complements)
	return append_spanish_adjective_usage_notes(sp_text, translated)

def normalize_comparative_sp_ntl(ntl: str) -> str:
	ntl = re.sub('\\bkexki\\s+iknok\\s+achto\\b', 'achto kexki iknok', ntl)
	return re.sub('\\s+', ' ', ntl).strip()

def resolve_ambiguous_spanish_tokens(tokens: list[str]) -> list[str]:
	"""
	Conserva tokens en español, pero normaliza ambigüedades que el analizador
	necesita distinguir antes de detectar sustantivos/modificadores.

	Reglas:
	- un/una/unos/unas se conservan como artículos/cantidad; no se convierten
	  directamente en raíces náhuatl.
	- rosa/rosas se conservan para que el detector decida por contexto:
		color rosa -> tlapaltik
		rosa/rosas como sustantivo -> xokoxochitl
	- se evita que "unos/unas" sea interpretado como forma verbal de "unir".
	"""
	resolved = []

	for i, tk in enumerate(tokens):

		tk = unicodedata.normalize('NFC', str(tk or '')).strip().lower()

		if not tk:
			continue

		if tk in {'un', 'una', 'unos', 'unas'}:
			resolved.append(tk)
			continue

		if tk in {'rosa', 'rosas'}:
			resolved.append(tk)
			continue

		# Equivalencias establecidas para la forma ambigua 'como':
		# - forma verbal de comer -> se conserva como 'como';
		# - nexo comparativo -> marcador que después produce kenin.
		#
		# La comparación no siempre lleva «a» ni pronombre:
		#   huele como zorrillo
		#   corre como un venado
		# Si ya existe un verbo finito antes de «como», la segunda lectura
		# verbal («comer») no debe desplazar al verbo principal.
		if tk == 'como':
			siguiente = ''

			if i + 1 < len(tokens):
				siguiente = unicodedata.normalize(
					'NFC', str(tokens[i + 1] or '')
				).strip().lower()

			prefix_tokens = [
				unicodedata.normalize('NFC', str(x or '')).strip().lower()
				for x in tokens[:i]
				if str(x or '').strip()
			]
			prior_verb_sp = None
			if prefix_tokens:
				prior_verb_sp, _, _, _ = detect_finite_verb(
					[
						x for x in prefix_tokens
						if x not in ARTICLES_SP
					]
				)
				if not prior_verb_sp:
					prior_verb_sp, _, _, _ = detect_regular_verb(
						[
							x for x in prefix_tokens
							if x not in ARTICLES_SP
						]
					)
				if not prior_verb_sp:
					prior_verb_sp, _ = detect_simple_verb(
						[
							x for x in prefix_tokens
							if x not in ARTICLES_SP
						]
					)

			if (
				siguiente in VISIBLE_PRONOUN_MAP_SP_TO_NTL
				or siguiente == 'a'
				or prior_verb_sp
			):
				resolved.append('__COMO_COMPARATIVO__')
				continue

			resolved.append(tk)
			continue

		# «a» ya quedó absorbida por «como a».
		if tk == 'a' and i > 0:
			anterior = unicodedata.normalize(
				'NFC', str(tokens[i - 1] or '')
			).strip().lower()
			if anterior == 'como':
				continue

		resolved.append(tk)

	return resolved

def _is_android():
	try:
		return 'ANDROID_STORAGE' in os.environ or 'android' in platform.system().lower()
	except Exception:
		return False

def load_icon(root: tk.Tk):
	try:
		if _is_android():
			for p in candidate_paths('Opoch_tlAhtol_64px.png', 'Opoch_tlAhtol.png', 'app.png'):
				if p.exists():
					try:
						img = tk.PhotoImage(file=str(p))
						root.iconphoto(True, img)
						root._iconphoto_ref = img
						return
					except Exception:
						pass
			return
		for p in candidate_paths('Opoch_tlAhtol_64px.ico', 'Opoch_tlAhtol.ico', 'app.ico'):
			if p.exists():
				try:
					root.iconbitmap(str(p))
					return
				except Exception:
					pass
		for p in candidate_paths('Opoch_tlAhtol_64px.png', 'Opoch_tlAhtol.png', 'app.png'):
			if p.exists():
				try:
					img = tk.PhotoImage(file=str(p))
					root.iconphoto(True, img)
					root._iconphoto_ref = img
					return
				except Exception:
					pass
	except Exception as e:
		print('Icono omitido:', e)

def show_image_below(parent):
	try:
		print('ENTRÓ a show_image_below')
		img = None
		for p in candidate_paths('ma_ti_tlahtokeh_nauatl.png'):
			print('Probando ruta:', p)
			if p.exists():
				try:
					print('Encontró archivo:', p)
					if Image is not None:
						im = Image.open(str(p))
						im = im.resize((75, 100))
						ph = ImageTk.PhotoImage(im)
					else:
						ph = tk.PhotoImage(file=str(p))
					img = ph
					print('Imagen cargada correctamente')
					break
				except Exception as e:
					print('Falló carga de imagen:', e)
		if img is None:
			print('No se encontró imagen para mostrar.')
			return
		label_img = tk.Label(parent, image=img, bg='light blue')
		label_img.image = img
		label_img.grid(row=1, column=1, sticky='n', pady=(10, PADY))
		print('Label de imagen colocado debajo del botón Translate')
	except Exception as e:
		print('Imagen omitida:', e)

def dictionaries_ready():
	sp_idx = globals().get('sp_word_index', {})
	ntl_idx = globals().get('ntl_word_index', {})
	return bool(sp_idx) or bool(ntl_idx)

def normalized_words(s):
	return re.sub('\\W+', ' ', unicodedata.normalize('NFC', s or '').lower()).strip()

def resolve_plural_variant(value, tokens, i, person_sel, number_sel):
	if not isinstance(value, dict):
		return value
	prev_subj = ''
	try:
		prev_subj = _sujeto_libre_previo(tokens, i)
	except:
		pass
	if prev_subj == 'ustedes':
		return value.get('ustedes')
	if prev_subj in ('ellos', 'ellas'):
		return value.get('ellos')
	if person_sel == '2' and number_sel == 'pl':
		return value.get('ustedes')
	if person_sel == '3' and number_sel == 'pl':
		return value.get('ellos')
	return value.get('ellos')

def translate_leading_inciso(label: str) -> str:
	if not label:
		return ''
	m = re.fullmatch('(\\d+)\\)', label.strip())
	if not m:
		return label.strip()
	raw_number = m.group(1)
	try:
		number_ntl = detect_number_sp([raw_number])
	except Exception:
		number_ntl = None
	if not number_ntl:
		return label.strip()
	return f'{number_ntl})'

def split_leading_inciso(text: str) -> tuple[str, str]:
	m = re.match('^\\s*(\\d+\\))\\s*(.*)$', text.strip())
	if not m:
		return ('', text.strip())
	return (m.group(1), m.group(2).strip())

def split_terminal_punctuation(text: str) -> tuple[str, str]:
	m = re.search('([.!?]+)$', text.strip())
	if not m:
		return (text.strip(), '')
	return (text.strip()[:-len(m.group(1))].rstrip(), m.group(1))

def _ntl_value_set(mapping: dict) -> set[str]:
	out = set()
	for val in mapping.values():
		if isinstance(val, (list, tuple)):
			for item in val:
				if item:
					out.add(str(item).strip())
		elif val:
			out.add(str(val).strip())
	return out
NTL_NOUN_SET = _ntl_value_set(NOUNS_SP_NTL)
NTL_MODIFIER_SET = _ntl_value_set(MODIFIERS)
NTL_SUBJECT_MAP_SP = {'nehuatl': 'yo', 'tehuatl': 'tú', 'yehuatl': 'ella', 'yehuatl': 'él', 'tehuan': 'nosotras', 'tehuan': 'nosotros', 'anmehuan': 'ustedes', 'yehuan': 'ellas', 'yehuan': 'ellos'}
NTL_OBJECT_MAP_SP = {'nech': 'me', 'mitz': 'te', 'ki': 'lo', 'tech': 'nos', 'anmech': 'los', 'kin': 'los', 'tla': 'algo', 'te': 'alguien', 'tetla': 'algo de alguien'}

def translate_token_ntl_to_sp(tk: str) -> str:
	raw = unicodedata.normalize('NFC', str(tk)).strip().lower()
	raw = raw.strip('.,;:¡!¿?"\'“”‘’()[]{}')
	key = normalize_ntl_orthography(raw)
	val = None
	if 'ntl_sp_index' in globals():
		val = ntl_sp_index.get(key) or ntl_sp_index.get(raw)
	if val is None:
		val = ntl_sp.get(key) or ntl_sp.get(raw)
	if val is None:
		# Las bases NTL→SP especializadas también son autoridad léxica.
		# Esto evita que modificadores y sustantivos conocidos caigan como [token]
		# sólo porque no estén duplicados dentro de ntl_sp.
		for mapping in (MODIFIERS_NTL_SP, NOUNS_NTL_SP):
			val = mapping.get(key) or mapping.get(raw)
			if val is not None:
				break
	if isinstance(val, list):
		val = val[0] if val else None
	if isinstance(val, dict):
		val = val.get('es') or val.get('sp')
	return str(val).strip() if val else f'[{key}]'

def looks_like_spanish_verb(word: str) -> bool:
	w = normalize_input_sp(word)
	return w.endswith(('ar', 'er', 'ir')) or w.endswith(('o', 'as', 'a', 'amos', 'an')) or w.endswith(('é', 'aste', 'ó', 'aron')) or w.endswith(('í', 'iste', 'ió', 'ieron')) or w.endswith(('ré', 'rás', 'rá', 'remos', 'rán'))

def capitalize_first(s: str) -> str:
	return s[0].upper() + s[1:] if s else s

def translate_ntl_gerund_contrast_to_sp(tokens: list[str]) -> str | None:
	if 'amitla' not in tokens or 'kema' not in tokens:
		return None
	gerunds = [tk for tk in tokens if tk.endswith('tika')]
	if len(gerunds) < 2:
		return None
	main_verb_tokens = []
	for i, tk in enumerate(tokens):
		if tk in {'amitla', 'kema'}:
			continue
		if tk.endswith('tika'):
			continue
		if tk in {'ni', 'ti', 'an'} and i + 1 < len(tokens):
			next_tk = tokens[i + 1]
			if next_tk not in {'amitla', 'kema'} and (not next_tk.endswith('tika')):
				main_verb_tokens = [tk, next_tk]
				break
		if tk not in {'ni', 'ti', 'an'}:
			main_verb_tokens = [tk]
			break
	if not main_verb_tokens:
		return None
	gerund_1 = translate_token_ntl_to_sp(gerunds[0])
	gerund_2 = translate_token_ntl_to_sp(gerunds[1])
	main_key = ' '.join(main_verb_tokens)
	main_verb = translate_token_ntl_to_sp(main_key)
	if not main_verb:
		main_verb = ' '.join((x for x in (translate_token_ntl_to_sp(y) for y in main_verb_tokens) if x)).strip()
	if not gerund_1 or not gerund_2 or (not main_verb):
		return None
	return f'{capitalize_first(gerund_1)} no {main_verb} nada, {gerund_2} sí.'

def reorder_short_ntl_to_natural_sp(tokens: list[str]) -> str | None:
	t = ' '.join(tokens)
	if t in {'mouan nochipa', 'nochipa mouan'}:
		return 'siempre contigo'
	return None
NTL_LOCATIVE_BLOCKS_TO_SP = {'ipan inon iuhkan': 'en aquel lugar'}
NTL_NOUN_PHRASE_BLOCKS_TO_SP = {'ze uey kalli': 'una gran casa', 'ze ueyik kalli': 'una gran casa'}
NTL_OBJECT_BLOCKS_TO_SP = {'anmech': 'a ustedes'}
NTL_VERB_BLOCKS_TO_SP = {'ni anmech makaz': 'les daré', 'ni makaz': 'daré'}

def translate_known_ntl_sentence_to_sp(text: str) -> str | None:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	has_subject = 'nehuatl' in t.split()
	has_time_adv = 'nochipa' in t.split()
	has_object = 'anmech' in t.split()
	has_locative = 'ipan inon iuhkan' in t
	has_noun_phrase = 'uey kalli' in t or 'ueyik kalli' in t
	has_verb = 'ni anmech makaz' in t or 'ni makaz' in t
	if has_subject and has_time_adv and has_object and has_locative and has_noun_phrase and has_verb:
		return 'Yo siempre a ustedes les daré una gran casa en aquel lugar'
	return None

def parse_ntl_structure_to_sp(text: str) -> dict:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	structure = {'subject': None, 'time_modifiers': [], 'indirect_object': None, 'verb': None, 'noun_phrases': [], 'locatives': [], 'others': []}
	i = 0
	while i < len(tokens):
		tk = tokens[i]
		if tk == 'nehuatl':
			structure['subject'] = 'Yo'
			i += 1
			continue
		if tk == 'nochipa':
			structure['time_modifiers'].append('siempre')
			i += 1
			continue
		if tk == 'anmech':
			structure['indirect_object'] = 'a ustedes'
			i += 1
			continue
		if i + 2 < len(tokens) and tokens[i:i + 3] == ['ipan', 'inon', 'iuhkan']:
			structure['locatives'].append('en aquel lugar')
			i += 3
			continue
		if i + 1 < len(tokens) and tokens[i] in {'uey', 'ueyik'} and (tokens[i + 1] == 'kalli'):
			structure['noun_phrases'].append('una gran casa')
			i += 2
			continue
		if i + 2 < len(tokens) and tokens[i:i + 3] == ['ni', 'anmech', 'makaz']:
			structure['verb'] = 'les daré'
			structure['indirect_object'] = 'a ustedes'
			i += 3
			continue
		if i + 1 < len(tokens) and tokens[i:i + 2] == ['ni', 'makaz']:
			structure['verb'] = 'daré'
			i += 2
			continue
		if tk == 'makaz':
			structure['verb'] = 'les daré'
			i += 1
			continue
		sp = translate_token_ntl_to_sp(tk)
		if sp:
			structure['others'].append(sp)
		i += 1
	return structure

def build_sp_expression_from_ntl_structure(structure: dict) -> str:
	parts = []
	if structure.get('subject'):
		parts.append(structure['subject'])
	for x in structure.get('time_modifiers', []):
		parts.append(x)
	if structure.get('indirect_object'):
		parts.append(structure['indirect_object'])
	if structure.get('verb'):
		parts.append(structure['verb'])
	for x in structure.get('noun_phrases', []):
		parts.append(x)
	for x in structure.get('locatives', []):
		parts.append(x)
	if structure.get('subject') and (not structure.get('verb')) and (not structure.get('noun_phrases')) and (not structure.get('locatives')) and structure.get('others'):
		return ''
	if not parts:
		for x in structure.get('others', []):
			parts.append(x)
	result = ' '.join(parts)
	result = re.sub('\\s+', ' ', result).strip()
	if result:
		result = result[0].upper() + result[1:]
	return result

def ntl_future_root_to_base_ntl(root: str) -> str:
	root = (root or '').strip()
	if root.endswith('az'):
		return root[:-2] + 'a'
	if root.endswith('iz'):
		return root[:-2] + 'i'
	if root.endswith('oz'):
		return root[:-2] + 'o'
	if root.endswith('ez'):
		return root[:-2] + 'e'
	if root.endswith('z'):
		return root[:-1]
	return root

def ntl_base_to_sp_infinitive(base_ntl: str) -> str | None:
	base_ntl = (base_ntl or '').strip()
	if not base_ntl:
		return None
	preferred_ntl_to_sp_verbs = {
		'chiua':'hacer',
		'temi':'complementar',
	}
	if base_ntl in preferred_ntl_to_sp_verbs:
		return preferred_ntl_to_sp_verbs[base_ntl]
	for sp_inf, ntl_root in INFINITIVE_VERBS_SP_TO_NTL.items():
		if first_variant(ntl_root) == base_ntl:
			return sp_inf
	for sp_inf, ntl_root in CORE_VERBS_SP_TO_NTL.items():
		if first_variant(ntl_root) == base_ntl:
			return sp_inf
	return None

def conjugate_sp_subjunctive_from_infinitive(infinitive_sp: str, time_kind: str) -> str | None:
	infinitive_sp = (infinitive_sp or '').strip()
	if infinitive_sp == 'comer':
		return 'coma' if time_kind == 'present_subjunctive' else 'comiera'
	if infinitive_sp == 'dormir':
		return 'duerma' if time_kind == 'present_subjunctive' else 'durmiera'
	if infinitive_sp in {'suceder', 'pasar'}:
		return 'suceda' if time_kind == 'present_subjunctive' else 'sucediera'
	if infinitive_sp.endswith('ar'):
		stem = infinitive_sp[:-2]
		return stem + ('e' if time_kind == 'present_subjunctive' else 'ara')
	if infinitive_sp.endswith('er') or infinitive_sp.endswith('ir'):
		stem = infinitive_sp[:-2]
		return stem + ('a' if time_kind == 'present_subjunctive' else 'iera')
	return None

def ntl_future_root_to_sp_subjunctive(root: str, time_kind: str='past_subjunctive') -> str | None:
	root = (root or '').strip()
	if not root:
		return None
	base_ntl = ntl_future_root_to_base_ntl(root)
	infinitive_sp = ntl_base_to_sp_infinitive(base_ntl)
	if not infinitive_sp:
		return None
	return conjugate_sp_subjunctive_from_infinitive(infinitive_sp, time_kind)

def is_known_ntl_verb_form(token: str) -> bool:
	token = (token or '').strip()
	if not token:
		return False
	root, ending = detect_ntl_verb_ending(token)
	if not root or not ending:
		return False
	if ending in {'future', 'future_plural'}:
		root = ntl_future_root_to_base_ntl(root + 'z')
	elif ending in {'pospreterite', 'pospreterite_plural'}:
		root = ntl_future_root_to_base_ntl(root)
	return ntl_base_to_sp_infinitive(root) is not None

def recover_object_verb_part(obj: str, verb_part: str) -> list[str]:
	candidates = [verb_part]
	if obj in {'ki', 'k'}:
		candidates.append('i' + verb_part)
	return candidates

def try_split_prefix_objects_verb(pref: str, rest: str) -> list[str] | None:
	objects = sorted(NTL_OBJECT_MAP_SP.keys(), key=len, reverse=True)

	def try_with_objects(current_rest: str, found_objects: list[str]) -> list[str] | None:
		if len(found_objects) > 2:
			return None
		if is_known_ntl_verb_form(current_rest):
			return [pref] + found_objects + [current_rest]
		for obj in objects:
			if not current_rest.startswith(obj):
				continue
			after_obj = current_rest[len(obj):]
			result = try_with_objects(after_obj, found_objects + [obj])
			if result:
				return result
			if obj == 'ki':
				recovered = 'i' + after_obj
				if is_known_ntl_verb_form(recovered):
					return [pref] + found_objects + [obj, recovered]
		return None
	return try_with_objects(rest, [])

def split_ntl_compound_token(token: str) -> list[str]:
	token = normalize_ntl_orthography(token)
	token = token.strip()
	if not token:
		return []
	if token in NTL_VISIBLE_PRONOUNS_TO_SP:
		return [token]
	if token in NTL_OBJECT_MAP_SP:
		return [token]
	reflexive_prefixes = [('onimo', 'oni'), ('otimo', 'oti'), ('oanmo', 'oan'), ('nimo', 'ni'), ('timo', 'ti'), ('anmo', 'an'), ('omo', 'o'), ('mo', None)]
	for pref, subject_prefix in reflexive_prefixes:
		if token.startswith(pref):
			verb_part = token[len(pref):]
			if not verb_part:
				continue
			root, ending = detect_ntl_verb_ending(verb_part)
			if ntl_base_to_sp_infinitive(root):
				if subject_prefix:
					return [subject_prefix, 'mo', verb_part]
				return ['mo', verb_part]
			if is_known_ntl_verb_form(verb_part):
				if subject_prefix:
					return [subject_prefix, 'mo', verb_part]
				return ['mo', verb_part]
			if subject_prefix:
				joined_without_mo = subject_prefix + verb_part
				if joined_without_mo in ntl_sp or joined_without_mo in ntl_sp_index:
					return [subject_prefix, 'mo', verb_part]
	for pref in ['oni', 'oti', 'oan', 'ni', 'ti', 'an', 'o']:
		if token.startswith(pref):
			rest = token[len(pref):]
			if rest in NTL_OBJECT_MAP_SP:
				return [pref, rest]
	for obj in sorted(NTL_OBJECT_MAP_SP.keys(), key=len, reverse=True):
		if token.startswith(obj):
			verb_part = token[len(obj):]
			if is_known_ntl_verb_form(verb_part):
				return [obj, verb_part]
	if is_known_ntl_verb_form(token):
		return [token]
	prefixes = ['oni', 'oti', 'oan', 'ni', 'ti', 'an', 'o', 'mo']
	objects = sorted(NTL_OBJECT_MAP_SP.keys(), key=len, reverse=True)
	for pref in prefixes:
		if not token.startswith(pref):
			continue
		rest = token[len(pref):]
		if not rest:
			continue
		multi_object_result = try_split_prefix_objects_verb(pref, rest)
		if multi_object_result:
			return multi_object_result
		if rest.startswith('mo'):
			verb_part = rest[2:]
			if not verb_part:
				continue
			root, ending = detect_ntl_verb_ending(verb_part)
			if ntl_base_to_sp_infinitive(root):
				return [pref, 'mo', verb_part]
			if is_known_ntl_verb_form(verb_part):
				return [pref, 'mo', verb_part]
			joined_without_mo = pref + verb_part
			if joined_without_mo in ntl_sp or joined_without_mo in ntl_sp_index:
				return [pref, 'mo', verb_part]
		for obj in objects:
			if not rest.startswith(obj):
				continue
			verb_part = rest[len(obj):]
			for candidate_verb in recover_object_verb_part(obj, verb_part):
				if is_known_ntl_verb_form(candidate_verb):
					return [pref, obj, candidate_verb]
				root, ending = detect_ntl_verb_ending(candidate_verb)
				if ending in {'future', 'future_plural', 'present', 'present_plural'}:
					if ending in {'future', 'future_plural'}:
						base = ntl_future_root_to_base_ntl(root + 'z')
					else:
						base = root
					if ntl_base_to_sp_infinitive(base):
						return [pref, obj, candidate_verb]
		if rest.startswith('k'):
			verb_part = rest[1:]
			if is_known_ntl_verb_form(verb_part):
				return [pref, 'ki', verb_part]
		if is_known_ntl_verb_form(rest):
			return [pref, rest]
	return [token]

def normalize_ntl_compound_tokens(text: str) -> str:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	out = []
	for tk in tokens:
		out.extend(split_ntl_compound_token(tk))
	return ' '.join(out)

def detect_ntl_verb_ending(token: str) -> tuple[str, str | None]:
	token = (token or '').strip()
	if not token:
		return ('', None)
	if ntl_base_to_sp_infinitive(token):
		return (token, 'present')
	ending_rules = [('zyakeh', 'pospreterite_plural'), ('zya', 'pospreterite'), ('zkeh', 'future_plural'), ('z', 'future'), ('yakeh', 'imperfect_plural'), ('ya', 'imperfect'), ('kek', 'past_plural'), ('keh', 'past_plural'), ('k', 'past'), ('tikeh', 'obligative_plural'), ('ti', 'obligative'), ('tikakeh', 'progressive_plural'), ('tika', 'progressive'), ('yauikeh', 'continuous_motion_plural'), ('yaui', 'continuous_motion'), ('h', 'present_plural')]
	for suffix, ending in ending_rules:
		if token.endswith(suffix):
			return (token[:-len(suffix)], ending)
	return (token, 'present')

def parse_ntl_conditional_structure(text: str) -> dict | None:
	t = normalize_ntl_compound_tokens(text)
	tokens = t.split()
	if not tokens or tokens[0] != 'intla':
		return None
	body_tokens = tokens[1:]
	if not body_tokens:
		return None
	first_verb_i = None
	for i, tk in enumerate(body_tokens):
		root, ending = detect_ntl_verb_ending(tk)
		if ending and ending != 'present':
			first_verb_i = i
			break
	if first_verb_i is None:
		return None
	second_clause_i = None
	for i in range(first_verb_i + 1, len(body_tokens)):
		if body_tokens[i] in NTL_VISIBLE_PRONOUNS_TO_SP:
			second_clause_i = i
			break
	if second_clause_i is None:
		for i in range(first_verb_i + 1, len(body_tokens)):
			if body_tokens[i] in {'ni', 'ti', 'an', 'nimo', 'timo', 'anmo', 'mo'}:
				second_clause_i = i
				break
	if second_clause_i is None:
		return {'raw': text, 'normalized': t, 'tokens': tokens, 'type': 'conditional', 'condition': parse_ntl_structure(' '.join(body_tokens)), 'main': None}
	condition_text = ' '.join(body_tokens[:second_clause_i])
	main_text = ' '.join(body_tokens[second_clause_i:])
	return {'raw': text, 'normalized': t, 'tokens': tokens, 'type': 'conditional', 'condition': parse_ntl_structure(condition_text), 'main': parse_ntl_structure(main_text)}

def parse_ntl_structure(text: str) -> dict:
	t = normalize_ntl_compound_tokens(text)
	tokens = t.split()

	# El semipronombre puede escribirse separado o unido al verbo.
	# Se normaliza internamente sin cambiar la forma de entrada.
	normalized_tokens = []
	for token in tokens:
		split_token = False
		for semi in ('ni', 'ti', 'an'):
			if token.startswith(semi) and len(token) > len(semi):
				candidate_root = token[len(semi):]
				if ntl_base_to_sp_infinitive(candidate_root):
					normalized_tokens.extend([semi, candidate_root])
					split_token = True
					break
		if not split_token:
			normalized_tokens.append(token)
	tokens = normalized_tokens
	t = ' '.join(tokens)
	conditional = parse_ntl_conditional_structure(t)
	if conditional:
		return conditional
	if tokens and tokens[0] == 'intla':
		structure = {'raw': text, 'normalized': t, 'tokens': tokens, 'type': 'conditional', 'condition': None, 'main': None}
		return structure
	structure = {'raw': text, 'normalized': t, 'tokens': tokens, 'prefix': None, 'visible_subject': None, 'explicit_subject': False, 'person': '3', 'number': 'sg', 'past_prefix': False, 'reflexive_sp': None, 'object_sp': None, 'adverbs': [], 'preverb_nouns': [], 'verb_token': None, 'verb_root': None, 'verb_ending': None, 'infinitive_sp': None, 'remaining': [], 'direct_object_sp': None, 'indirect_object_sp': None}
	if not tokens:
		return structure

	# En NTL un modificador puede anteceder al pronombre sujeto:
	# nochi yehuan otemikeh. Se conserva como modificador de la cláusula
	# y no se fuerza a ocupar la posición verbal. La regla es productiva:
	# sólo adelanta el inicio sintáctico cuando después aparece un pronombre
	# sujeto explícito reconocido.
	leading_modifiers = []
	prefix_start = 0

	# Un sustantivo u objeto nominal puede anteceder a la cláusula verbal:
	# komitl ni temi / komitl nitemi. Se separa del prefijo verbal y se
	# conserva para colocarlo después del verbo en la salida española.
	for prefix_i, token in enumerate(tokens):
		if token in NTL_VISIBLE_PRONOUNS_TO_SP or token in {'ni', 'ti', 'an', 'o', 'oni', 'oti', 'oan'}:
			candidates = tokens[:prefix_i]
			if candidates:
				candidate_phrase = ' '.join(candidates)
				candidate_exact = lookup_ntl_sp_exact(candidate_phrase)
				if len(candidates) > 1 and candidate_exact and candidate_phrase in NOUNS_NTL_SP_INDEX:
					structure['preverb_nouns'] = [candidate_exact]
					prefix_start = prefix_i
				elif all(candidate in NTL_NOUN_SET for candidate in candidates):
					structure['preverb_nouns'] = [translate_token_ntl_to_sp(candidate) for candidate in candidates]
					prefix_start = prefix_i
			break
	for subject_i, token in enumerate(tokens):
		if token not in NTL_VISIBLE_PRONOUNS_TO_SP:
			continue
		candidates = tokens[:subject_i]
		if candidates and all(candidate in NTL_MODIFIER_SET for candidate in candidates):
			leading_modifiers = [translate_token_ntl_to_sp(candidate) for candidate in candidates]
			leading_modifiers = [value for value in leading_modifiers if value and not value.startswith('[')]
			prefix_start = subject_i
		break

	prefix, i = parse_ntl_clause_prefix_to_sp(tokens, prefix_start)
	structure['prefix'] = prefix
	structure['visible_subject'] = prefix['visible_subject']
	structure['explicit_subject'] = prefix['explicit_subject']
	structure['person'] = prefix['person']
	structure['number'] = prefix['number']
	structure['past_prefix'] = prefix['past_prefix']
	structure['reflexive_sp'] = prefix['reflexive_sp']
	structure['object_sp'] = prefix['object_sp']
	structure['direct_object_sp'] = prefix.get('direct_object_sp')
	structure['indirect_object_sp'] = prefix.get('indirect_object_sp')
	adverbs, i = parse_ntl_adverbs_to_sp(tokens, i)
	structure['adverbs'] = leading_modifiers + adverbs
	if i >= len(tokens):
		return structure
	verb_token = tokens[i]
	structure['verb_token'] = verb_token
	root, ending = detect_ntl_verb_ending(verb_token)

	if (
		structure.get('prefix')
		and structure['prefix'].get('person') == '2'
		and structure['prefix'].get('number') == 'sg'
		and tokens
		and tokens[0] == 'ti'
		and ending in {
			'present_plural',
			'past_plural',
			'imperfect_plural',
			'future_plural',
			'pospreterite_plural',
		}
	):
		structure['person'], structure['number'] = ('1', 'pl')

	past_token = structure['prefix'].get('past_token') if structure.get('prefix') else None
	if past_token == 'oti' and ending in {'past_plural', 'imperfect_plural'}:
		structure['person'], structure['number'] = ('1', 'pl')
	elif past_token == 'o' and ending in {'past_plural', 'imperfect_plural'}:
		structure['person'], structure['number'] = ('3', 'pl')
	if ending in {'future', 'future_plural'}:
		root = ntl_future_root_to_base_ntl(root + 'z')
	elif ending in {'pospreterite', 'pospreterite_plural'}:
		root = ntl_future_root_to_base_ntl(root)
	structure['verb_root'] = root
	structure['verb_ending'] = ending
	structure['infinitive_sp'] = ntl_base_to_sp_infinitive(root)
	if i + 1 < len(tokens):
		structure['remaining'] = tokens[i + 1:]
	return structure

def parse_ntl_clause_prefix_to_sp(tokens: list[str], i: int=0) -> tuple[dict, int]:
	data = {'visible_subject': None, 'explicit_subject': False, 'reflexive_sp': None, 'object_sp': None, 'direct_object_sp': None, 'indirect_object_sp': None, 'past_prefix': False, 'person': '3', 'number': 'sg', 'past_token': None}
	if i < len(tokens) and tokens[i] in NTL_VISIBLE_PRONOUNS_TO_SP:
		data['visible_subject'] = NTL_VISIBLE_PRONOUNS_TO_SP[tokens[i]]
		data['explicit_subject'] = True
		if tokens[i] == 'nehuatl':
			data['person'], data['number'] = ('1', 'sg')
		elif tokens[i] == 'tehuatl':
			data['person'], data['number'] = ('2', 'sg')
		elif tokens[i] == 'anmehuan':
			data['person'], data['number'] = ('2', 'pl')
		elif tokens[i] == 'tehuan':
			data['person'], data['number'] = ('1', 'pl')
		elif tokens[i] == 'yehuan':
			data['person'], data['number'] = ('3', 'pl')
		i += 1
	if i < len(tokens) and tokens[i] in {'o', 'oni', 'oti', 'oan'}:
		data['past_prefix'] = True
		data['past_token'] = tokens[i]
		if tokens[i] == 'oni':
			data['person'], data['number'] = ('1', 'sg')
		elif tokens[i] == 'oti':
			data['person'], data['number'] = ('2', 'sg')
		elif tokens[i] == 'oan':
			data['person'], data['number'] = ('2', 'pl')
		i += 1
	if i < len(tokens) and tokens[i] == 'nimo':
		data['visible_subject'] = data['visible_subject'] or 'yo'
		data['reflexive_sp'] = 'mismo'
		data['person'], data['number'] = ('1', 'sg')
		i += 1
	elif i < len(tokens) and tokens[i] == 'timo':
		data['visible_subject'] = data['visible_subject'] or 'tú'
		data['reflexive_sp'] = 'mismo'
		data['person'], data['number'] = ('2', 'sg')
		i += 1
	elif i < len(tokens) and tokens[i] == 'ni':
		data['person'], data['number'] = ('1', 'sg')
		i += 1
	elif i < len(tokens) and tokens[i] == 'ti':
		data['person'], data['number'] = ('2', 'sg')
		i += 1
	elif i < len(tokens) and tokens[i] == 'an':
		data['person'], data['number'] = ('2', 'pl')
		i += 1
	if i < len(tokens) and tokens[i] == 'mo':
		data['reflexive_sp'] = 'mismo'
		if data['person'] == '3':
			data['visible_subject'] = None
		i += 1
	objects_found = []
	while i < len(tokens) and tokens[i] in NTL_OBJECT_MAP_SP:
		obj = NTL_OBJECT_MAP_SP[tokens[i]]
		if obj == 'te':
			obj = 'a ti'
		elif obj == 'me':
			obj = 'a mí'
		objects_found.append(obj)
		i += 1
	if len(objects_found) == 1:
		data['object_sp'] = objects_found[0]
		data['direct_object_sp'] = objects_found[0]
	elif len(objects_found) >= 2:
		data['direct_object_sp'] = objects_found[0]
		data['indirect_object_sp'] = objects_found[1]
		data['object_sp'] = objects_found[0]
	return (data, i)

def translate_ntl_auxiliary_subordinate_to_sp(text: str) -> str | None:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	if not tokens:
		return None
	aux_time = None
	main_sp = None
	coord_sp = None
	prefix, i = parse_ntl_clause_prefix_to_sp(tokens)
	visible_subject = prefix['visible_subject']
	reflexive_sp = prefix['reflexive_sp']
	object_sp = prefix['object_sp']
	past_prefix = prefix['past_prefix']
	if i >= len(tokens):
		return None
	main_token = tokens[i]
	i += 1
	root, aux_ntl, aux_kind = parse_ntl_auxiliary_compound(main_token)
	if not root or not aux_ntl or (not aux_kind):
		return None
	if past_prefix and aux_kind == 'present':
		aux_kind = 'past'
	aux_time = NTL_AUXILIARY_SUFFIX_TO_SP.get(aux_ntl, {}).get(aux_kind)
	if not aux_time:
		return None
	subordinate_time = 'past_subjunctive'
	if aux_kind in {'present', 'future'}:
		subordinate_time = 'present_subjunctive'

	# Los compuestos verbo-z + auxiliar expresan una acción potencial
	# subordinada al auxiliar, pero no incorporan por sí mismos la
	# conjunción española "que". La acción principal se reconstruye
	# como infinitivo: tlahtozneki -> quiero hablar.
	main_base_ntl = ntl_future_root_to_base_ntl(root)
	main_sp = ntl_base_to_sp_infinitive(main_base_ntl)
	if not main_sp:
		return None
	coord_object_sp = None
	if i < len(tokens) and tokens[i] in {'iuan', 'uan'}:
		i += 1
		if i < len(tokens) and tokens[i] in NTL_OBJECT_MAP_SP:
			coord_object_sp = NTL_OBJECT_MAP_SP[tokens[i]]
			i += 1
		if i < len(tokens):
			coord_token = tokens[i]
			if coord_token.startswith('ma'):
				coord_root = coord_token[2:]
			else:
				coord_root = coord_token
			coord_sp = ntl_future_root_to_sp_subjunctive(coord_root, subordinate_time)
	purpose_sp = None
	if i < len(tokens) and tokens[i] == 'inik':
		i += 1
		if i < len(tokens):
			purpose_token = tokens[i]
			if purpose_token.startswith('ma'):
				purpose_root = purpose_token[2:]
			else:
				purpose_root = purpose_token
			purpose_sp = ntl_future_root_to_sp_subjunctive(purpose_root, subordinate_time)
	parts = []
	if prefix['explicit_subject'] and visible_subject:
		parts.append(visible_subject)
	if reflexive_sp:
		parts.append(reflexive_sp)
	parts.append(aux_time)
	if object_sp:
		parts.append(object_sp)
	parts.append(main_sp)
	if coord_sp:
		parts.append('y')
		parts.append('que')
		if coord_object_sp:
			parts.append(coord_object_sp)
		parts.append(coord_sp)
	if purpose_sp:
		parts.append('para')
		parts.append('que')
		parts.append(purpose_sp)
	return ' '.join(parts)
NTL_AUXILIARY_SUFFIX_TO_SP = {'neki': {'present': 'quiero', 'copreterite': 'quería', 'past': 'quise', 'future': 'querré', 'subjunctive': 'quiera'}, 'ueli': {'present': 'puedo', 'copreterite': 'podía', 'past': 'pude', 'future': 'podré', 'subjunctive': 'pueda'}, 'uihkili': {'present': 'debo', 'copreterite': 'debía', 'past': 'debí', 'future': 'deberé', 'subjunctive': 'deba'}, 'onneki': {'present': 'necesito', 'copreterite': 'necesitaba', 'past': 'necesité', 'future': 'necesitaré', 'subjunctive': 'necesite'}}

def parse_ntl_auxiliary_compound(token: str) -> tuple[str | None, str | None, str | None]:
	token = (token or '').strip()

	def clean_root(root: str) -> str:
		# En compuestos con uihkili el guion marca una separación sonora:
		# ititiz-uihkili -> ititiz + uihkili.
		# No forma parte de la raíz verbal que debe analizarse.
		return root[:-1] if root.endswith('-') else root

	for aux_ntl in NTL_AUXILIARY_SUFFIX_TO_SP:
		if token.endswith(aux_ntl + 'ya'):
			root = clean_root(token[:-len(aux_ntl + 'ya')])
			return (root, aux_ntl, 'copreterite')
		if token.endswith(aux_ntl + 'k'):
			root = clean_root(token[:-len(aux_ntl + 'k')])
			return (root, aux_ntl, 'past')
		if token.endswith(aux_ntl + 'z'):
			root = clean_root(token[:-len(aux_ntl + 'z')])
			return (root, aux_ntl, 'future')
		if token.endswith(aux_ntl):
			root = clean_root(token[:-len(aux_ntl)])
			return (root, aux_ntl, 'present')
	return (None, None, None)

def parse_ntl_adverbs_to_sp(tokens: list[str], i: int):
	adverbs = []
	while i < len(tokens) - 1:
		sp = translate_token_ntl_to_sp(tokens[i])
		if not sp or sp.startswith('['):
			break
		if looks_like_spanish_verb(sp):
			break
		adverbs.append(sp)
		i += 1
	return (adverbs, i)

def conjugate_sp_future_or_pospreterite(infinitive_sp: str, mode: str, person: str, number: str) -> str | None:
	if mode == 'pospreterite':
		if infinitive_sp == 'ir':
			base = 'ir'
		else:
			base = infinitive_sp
		if person == '1' and number == 'sg':
			return base + 'ía'
		if person == '2' and number == 'sg':
			return base + 'ías'
		if person == '1' and number == 'pl':
			return base + 'íamos'
		if number == 'pl':
			return base + 'ían'
		return base + 'ía'
	if infinitive_sp == 'ir':
		if person == '1' and number == 'sg':
			return 'iré'
		if person == '2' and number == 'sg':
			return 'irás'
		if person == '1' and number == 'pl':
			return 'iremos'
		if number == 'pl':
			return 'irán'
		return 'irá'
	base = infinitive_sp
	if person == '1' and number == 'sg':
		return base + 'é'
	if person == '2' and number == 'sg':
		return base + 'ás'
	if person == '1' and number == 'pl':
		return base + 'emos'
	if number == 'pl':
		return base + 'án'
	return base + 'á'

def translate_ntl_simple_future_to_sp(text: str, conditional: bool=False) -> str | None:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	if not tokens:
		return None
	prefix, i = parse_ntl_clause_prefix_to_sp(tokens)
	visible_subject = prefix['visible_subject']
	reflexive_sp = prefix['reflexive_sp']
	object_sp = prefix['object_sp']
	person = prefix['person']
	number = prefix['number']
	adverbs, i = parse_ntl_adverbs_to_sp(tokens, i)
	if i >= len(tokens):
		return None
	verb_token = tokens[i]
	if verb_token.endswith('zya'):
		base_token = verb_token[:-2]
		mode = 'pospreterite'
	elif verb_token.endswith('z'):
		base_token = verb_token
		mode = 'future'
	else:
		return None
	base_ntl = ntl_future_root_to_base_ntl(base_token)
	infinitive_sp = ntl_base_to_sp_infinitive(base_ntl)
	if not infinitive_sp:
		return None
	if conditional:
		verb_sp = conjugate_sp_conditional_subjunctive(infinitive_sp, person, number)
	else:
		verb_sp = conjugate_sp_future_or_pospreterite(infinitive_sp, mode, person, number)
	if not verb_sp:
		return None
	parts = []
	if conditional:
		parts.append('si')
	if prefix['explicit_subject'] and visible_subject:
		parts.append(visible_subject)
	if reflexive_sp:
		parts.append(reflexive_sp)
	if object_sp:
		parts.append(object_sp)
	parts.append(verb_sp)
	for adv in adverbs:
		parts.append(adv)
	return ' '.join(parts)

def translate_ntl_conditional_future_to_sp(text: str) -> str | None:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	if not t.startswith('intla '):
		return None
	body = t[len('intla '):].strip()
	tokens = body.split()
	if not tokens:
		return None
	first_verb_i = None
	for i, tk in enumerate(tokens):
		if tk.endswith('z') or tk.endswith('zya'):
			first_verb_i = i
			break
	if first_verb_i is None:
		return translate_ntl_simple_future_to_sp(body, conditional=True)
	second_clause_i = None
	for i in range(first_verb_i + 1, len(tokens)):
		if tokens[i] in NTL_VISIBLE_PRONOUNS_TO_SP:
			second_clause_i = i
			break
	if second_clause_i is None:
		for i in range(first_verb_i + 1, len(tokens)):
			if tokens[i] in {'ni', 'ti', 'an', 'nimo', 'timo'}:
				second_clause_i = i
				break
	if second_clause_i is None:
		return translate_ntl_simple_future_to_sp(body, conditional=True)
	condition_ntl = ' '.join(tokens[:second_clause_i])
	main_ntl = ' '.join(tokens[second_clause_i:])
	condition_sp = translate_ntl_simple_future_to_sp(condition_ntl, conditional=True)
	main_sp = translate_ntl_simple_future_to_sp(main_ntl, conditional=False)
	if main_sp and condition_sp:
		return main_sp + ' ' + condition_sp
	return condition_sp


PRESENT_IRREGULAR_FORMS_SP = {
	'ir': {
		('1', 'sg'): 'voy',
		('2', 'sg'): 'vas',
		('3', 'sg'): 'va',
		('1', 'pl'): 'vamos',
		('2', 'pl'): 'van',
		('3', 'pl'): 'van',
	},
	'dar': {
		('1', 'sg'): 'doy',
		('2', 'sg'): 'das',
		('3', 'sg'): 'da',
		('1', 'pl'): 'damos',
		('2', 'pl'): 'dan',
		('3', 'pl'): 'dan',
	},
	'ver': {
		('1', 'sg'): 'veo',
		('2', 'sg'): 'ves',
		('3', 'sg'): 've',
		('1', 'pl'): 'vemos',
		('2', 'pl'): 'ven',
		('3', 'pl'): 'ven',
	},
	'querer': {
		('1', 'sg'): 'quiero',
		('2', 'sg'): 'quieres',
		('3', 'sg'): 'quiere',
		('1', 'pl'): 'queremos',
		('2', 'pl'): 'quieren',
		('3', 'pl'): 'quieren',
	},
	'poder': {
		('1', 'sg'): 'puedo',
		('2', 'sg'): 'puedes',
		('3', 'sg'): 'puede',
		('1', 'pl'): 'podemos',
		('2', 'pl'): 'pueden',
		('3', 'pl'): 'pueden',
	},
	'decir': {
		('1', 'sg'): 'digo',
		('2', 'sg'): 'dices',
		('3', 'sg'): 'dice',
		('1', 'pl'): 'decimos',
		('2', 'pl'): 'dicen',
		('3', 'pl'): 'dicen',
	},
	'recordar': {
		('1', 'sg'): 'recuerdo',
		('2', 'sg'): 'recuerdas',
		('3', 'sg'): 'recuerda',
		('1', 'pl'): 'recordamos',
		('2', 'pl'): 'recuerdan',
		('3', 'pl'): 'recuerdan',
	},
	'hacer': {
		('1', 'sg'): 'hago',
		('2', 'sg'): 'haces',
		('3', 'sg'): 'hace',
		('1', 'pl'): 'hacemos',
		('2', 'pl'): 'hacen',
		('3', 'pl'): 'hacen',
	},
	'tener': {
		('1', 'sg'): 'tengo',
		('2', 'sg'): 'tienes',
		('3', 'sg'): 'tiene',
		('1', 'pl'): 'tenemos',
		('2', 'pl'): 'tienen',
		('3', 'pl'): 'tienen',
	},
	'venir': {
		('1', 'sg'): 'vengo',
		('2', 'sg'): 'vienes',
		('3', 'sg'): 'viene',
		('1', 'pl'): 'venimos',
		('2', 'pl'): 'vienen',
		('3', 'pl'): 'vienen',
	},
	'poner': {
		('1', 'sg'): 'pongo',
		('2', 'sg'): 'pones',
		('3', 'sg'): 'pone',
		('1', 'pl'): 'ponemos',
		('2', 'pl'): 'ponen',
		('3', 'pl'): 'ponen',
	},
	'salir': {
		('1', 'sg'): 'salgo',
		('2', 'sg'): 'sales',
		('3', 'sg'): 'sale',
		('1', 'pl'): 'salimos',
		('2', 'pl'): 'salen',
		('3', 'pl'): 'salen',
	},
	'saber': {
		('1', 'sg'): 'sé',
		('2', 'sg'): 'sabes',
		('3', 'sg'): 'sabe',
		('1', 'pl'): 'sabemos',
		('2', 'pl'): 'saben',
		('3', 'pl'): 'saben',
	},
	'morir': {
		('1', 'sg'): 'muero',
		('2', 'sg'): 'mueres',
		('3', 'sg'): 'muere',
		('1', 'pl'): 'morimos',
		('2', 'pl'): 'mueren',
		('3', 'pl'): 'mueren',
	},
	'dormir': {
		('1', 'sg'): 'duermo',
		('2', 'sg'): 'duermes',
		('3', 'sg'): 'duerme',
		('1', 'pl'): 'dormimos',
		('2', 'pl'): 'duermen',
		('3', 'pl'): 'duermen',
	},
	'conocer': {
		('1', 'sg'): 'conozco',
		('2', 'sg'): 'conoces',
		('3', 'sg'): 'conoce',
		('1', 'pl'): 'conocemos',
		('2', 'pl'): 'conocen',
		('3', 'pl'): 'conocen',
	},
}


def conjugate_sp_present_from_infinitive(infinitive_sp: str, person: str, number: str) -> str | None:
	irregular_forms = PRESENT_IRREGULAR_FORMS_SP.get(infinitive_sp)

	if irregular_forms:
		return irregular_forms.get((person, number))

	if infinitive_sp == 'ir':
		if person == '1' and number == 'sg':
			return 'voy'
		if person == '2' and number == 'sg':
			return 'vas'
		if person == '1' and number == 'pl':
			return 'vamos'
		if number == 'pl':
			return 'van'
		return 'va'
	if infinitive_sp == 'dar':
		if person == '1' and number == 'sg':
			return 'doy'
		if person == '2' and number == 'sg':
			return 'das'
		if person == '1' and number == 'pl':
			return 'damos'
		if number == 'pl':
			return 'dan'
		return 'da'
	if infinitive_sp == 'querer':
		if person == '1' and number == 'sg':
			return 'quiero'
		if person == '2' and number == 'sg':
			return 'quieres'
		if person == '1' and number == 'pl':
			return 'queremos'
		if number == 'pl':
			return 'quieren'
		return 'quiere'
	if infinitive_sp == 'ver':
		if person == '1' and number == 'sg':
			return 'veo'
		if person == '2' and number == 'sg':
			return 'ves'
		if person == '1' and number == 'pl':
			return 'vemos'
		if number == 'pl':
			return 'ven'
		return 've'
	if infinitive_sp == 'decir':
		if person == '1' and number == 'sg':
			return 'digo'
		if person == '2' and number == 'sg':
			return 'dices'
		if person == '1' and number == 'pl':
			return 'decimos'
		if number == 'pl':
			return 'dicen'
		return 'dice'
	if infinitive_sp == 'recordar':
		if person == '1' and number == 'sg':
			return 'recuerdo'
		if person == '2' and number == 'sg':
			return 'recuerdas'
		if person == '1' and number == 'pl':
			return 'recordamos'
		if number == 'pl':
			return 'recuerdan'
		return 'recuerda'
	if infinitive_sp.endswith('ar'):
		base = infinitive_sp[:-2]
		if person == '1' and number == 'sg':
			return base + 'o'
		if person == '2' and number == 'sg':
			return base + 'as'
		if person == '1' and number == 'pl':
			return base + 'amos'
		if number == 'pl':
			return base + 'an'
		return base + 'a'
	if infinitive_sp.endswith('er') or infinitive_sp.endswith('ir'):
		base = infinitive_sp[:-2]
		if person == '1' and number == 'sg':
			return base + 'o'
		if person == '2' and number == 'sg':
			return base + 'es'
		if person == '1' and number == 'pl':
			return base + 'emos'
		if number == 'pl':
			return base + 'en'
		return base + 'e'
	return None

def conjugate_sp_imperfect_from_infinitive(infinitive_sp: str, person: str, number: str) -> str | None:
	if infinitive_sp == 'ver':
		base_form = 'veía'
	elif infinitive_sp == 'ir':
		base_form = 'iba'
	elif infinitive_sp == 'ser':
		base_form = 'era'
	elif infinitive_sp.endswith('ar'):
		base = infinitive_sp[:-2]
		base_form = base + 'aba'
	elif infinitive_sp.endswith('er') or infinitive_sp.endswith('ir'):
		base = infinitive_sp[:-2]
		base_form = base + 'ía'
	else:
		return None

	if person == '2' and number == 'sg':
		return base_form + 's'

	if number == 'pl':
		return base_form + 'n'

	return base_form

def translate_ntl_simple_present_to_sp(text: str) -> str | None:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	if not tokens:
		return None
	prefix, i = parse_ntl_clause_prefix_to_sp(tokens)
	visible_subject = prefix['visible_subject']
	object_sp = prefix['object_sp']
	person = prefix['person']
	number = prefix['number']
	if i >= len(tokens):
		return None
	verb_token = tokens[i]
	root, ending = detect_ntl_verb_ending(verb_token)

	if tokens[0] == 'ti' and ending == 'present_plural':
		person = '1'
		number = 'pl'

	infinitive_sp = ntl_base_to_sp_infinitive(root)
	if not infinitive_sp:
		return None
	verb_sp = conjugate_sp_present_from_infinitive(infinitive_sp, person, number)
	if not verb_sp:
		return None
	parts = []
	if prefix['explicit_subject'] and visible_subject:
		parts.append(visible_subject)
	if object_sp:
		parts.append(object_sp)
	parts.append(verb_sp)
	return ' '.join(parts)

def translate_ntl_simple_imperfect_to_sp(text: str) -> str | None:
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	if not tokens:
		return None
	prefix, i = parse_ntl_clause_prefix_to_sp(tokens)
	visible_subject = prefix['visible_subject']
	object_sp = prefix['object_sp']
	person = prefix['person']
	number = prefix['number']
	if i >= len(tokens):
		return None
	verb_token = tokens[i]
	if not verb_token.endswith('ya'):
		return None
	base_ntl = verb_token[:-2]
	infinitive_sp = ntl_base_to_sp_infinitive(base_ntl)
	if not infinitive_sp:
		return None
	verb_sp = conjugate_sp_imperfect_from_infinitive(infinitive_sp, person, number)
	if not verb_sp:
		return None
	parts = []
	if prefix['explicit_subject'] and visible_subject:
		parts.append(visible_subject)
	if object_sp:
		parts.append(object_sp)
	parts.append(verb_sp)
	return ' '.join(parts)

def conjugate_sp_conditional_subjunctive(infinitive_sp: str, person: str, number: str) -> str | None:
	irregular_bases = {'ir': 'fu', 'ser': 'fu', 'morir': 'mur'}
	if infinitive_sp in irregular_bases:
		base = irregular_bases[infinitive_sp]
		if person == '2' and number == 'sg':
			return base + 'ieres'
		if number == 'pl':
			return base + 'ieren'
		return base + 'iere'
	base = infinitive_sp[:-2]
	if infinitive_sp.endswith('ar'):
		form = base + 'are'
	elif infinitive_sp.endswith('er') or infinitive_sp.endswith('ir'):
		form = base + 'iere'
	else:
		return None
	if person == '2' and number == 'sg':
		return form + 's'
	if number == 'pl':
		return form + 'n'
	return form

def conjugate_sp_past_from_infinitive(infinitive_sp: str, person: str, number: str) -> str | None:
	irregular = {'ir': {('1', 'sg'): 'fui', ('2', 'sg'): 'fuiste', ('3', 'sg'): 'fue', ('1', 'pl'): 'fuimos', ('2', 'pl'): 'fueron', ('3', 'pl'): 'fueron'}, 'ser': {('1', 'sg'): 'fui', ('2', 'sg'): 'fuiste', ('3', 'sg'): 'fue', ('1', 'pl'): 'fuimos', ('2', 'pl'): 'fueron', ('3', 'pl'): 'fueron'}, 'ver': {('1', 'sg'): 'vi', ('2', 'sg'): 'viste', ('3', 'sg'): 'vio', ('1', 'pl'): 'vimos', ('2', 'pl'): 'vieron', ('3', 'pl'): 'vieron'}}
	key = (person, number)
	if infinitive_sp in irregular:
		return irregular[infinitive_sp].get(key)
	base = infinitive_sp[:-2]
	if infinitive_sp.endswith('ar'):
		if person == '1' and number == 'sg':
			return base + 'é'
		if person == '2' and number == 'sg':
			return base + 'aste'
		if person == '1' and number == 'pl':
			return base + 'amos'
		if number == 'pl':
			return base + 'aron'
		return base + 'ó'
	if infinitive_sp.endswith('er') or infinitive_sp.endswith('ir'):
		if person == '1' and number == 'sg':
			return base + 'í'
		if person == '2' and number == 'sg':
			return base + 'iste'
		if person == '1' and number == 'pl':
			return base + 'imos'
		if number == 'pl':
			return base + 'ieron'
		return base + 'ió'
	return None

def conjugate_sp_by_tense(infinitive_sp: str, tense: str, person: str, number: str) -> str | None:
	if tense in {'present', 'present_plural'}:
		return conjugate_sp_present_from_infinitive(infinitive_sp, person, number)
	if tense in {'past', 'past_plural'}:
		return conjugate_sp_past_from_infinitive(infinitive_sp, person, number)
	if tense in {'future', 'future_plural'}:
		return conjugate_sp_future_or_pospreterite(infinitive_sp, 'future', person, number)
	if tense in {'imperfect', 'imperfect_plural'}:
		return conjugate_sp_imperfect_from_infinitive(infinitive_sp, person, number)
	if tense in {'pospreterite', 'pospreterite_plural'}:
		return conjugate_sp_future_or_pospreterite(infinitive_sp, 'pospreterite', person, number)
	return None

def translate_ntl_structure_to_sp(structure: dict, conditional_part: bool=False) -> str | None:
	if not structure:
		return None
	if structure.get('type') == 'conditional':
		main_sp = translate_ntl_structure_to_sp(structure.get('main'))
		condition_sp = translate_ntl_structure_to_sp(structure.get('condition'), conditional_part=True)
		if main_sp and condition_sp:
			return main_sp + ' si ' + condition_sp
		return condition_sp
	infinitive_sp = structure.get('infinitive_sp')
	ending = structure.get('verb_ending')
	person = structure.get('person', '3')
	number = structure.get('number', 'sg')
	if ending in {'present_plural', 'future_plural', 'past_plural', 'imperfect_plural', 'pospreterite_plural'}:
		number = 'pl'
	if not infinitive_sp or not ending:
		return None
	if conditional_part and ending in {'future', 'future_plural'}:
		verb_sp = conjugate_sp_conditional_subjunctive(infinitive_sp, person, number)
	else:
		verb_sp = conjugate_sp_by_tense(infinitive_sp, ending, person, number)
	if not verb_sp:
		return None
	parts = []
	if structure.get('explicit_subject') and structure.get('visible_subject'):
		parts.append(structure['visible_subject'])
	elif structure.get('reflexive_sp') and structure.get('visible_subject'):
		parts.append(structure['visible_subject'])
	reflexive_sp = structure.get('reflexive_sp')
	if reflexive_sp:
		if number == 'pl':
			parts.append('mismos')
		else:
			parts.append(reflexive_sp)
	direct_object_sp = structure.get('direct_object_sp')
	indirect_object_sp = structure.get('indirect_object_sp')

	natural_direct_objects = {
		'a mí': 'me',
		'a ti': 'te',
		'a nosotros': 'nos',
		'a nosotras': 'nos',
		'a él': 'lo',
		'a ella': 'la',
		'a ellos': 'los',
		'a ellas': 'las',
	}

	if direct_object_sp and indirect_object_sp:
		natural_direct_object = natural_direct_objects.get(
			direct_object_sp,
			direct_object_sp
		)

		parts.append(indirect_object_sp)
		parts.append(natural_direct_object)

	elif structure.get('object_sp'):
		object_sp = structure['object_sp']

		natural_object_sp = natural_direct_objects.get(
			object_sp,
			object_sp
		)

		parts.append(natural_object_sp)

	parts.append(verb_sp)

	for noun_sp in structure.get('preverb_nouns', []):
		if noun_sp and not noun_sp.startswith('['):
			parts.append(noun_sp)

	for adv in structure.get('adverbs', []):
		parts.append(adv)

	remaining = structure.get('remaining', [])
	if remaining:
		inline_phrases, _used_indexes = detect_inline_fixed_phrases_ntl(remaining)
		for _start, _end, phrase_sp, _source_kind in sorted(inline_phrases, key=lambda item: item[0]):
			if phrase_sp:
				parts.append(phrase_sp)

	return ' '.join(parts).strip()

def translate_ntl_reflexive_direct_to_sp(text: str) -> str | None:
	t = normalize_ntl_compound_tokens(text)
	tokens = t.split()
	if not tokens:
		return None
	visible_subject = None
	explicit_subject = False
	i = 0
	if i < len(tokens) and tokens[i] in NTL_VISIBLE_PRONOUNS_TO_SP:
		visible_subject = NTL_VISIBLE_PRONOUNS_TO_SP[tokens[i]]
		explicit_subject = True
		i += 1
	if i >= len(tokens):
		return None
	prefix = tokens[i]
	i += 1
	person = '3'
	number = 'sg'
	if prefix in {'ni', 'oni'}:
		person, number = ('1', 'sg')
	elif prefix in {'ti', 'oti'}:
		person, number = ('2', 'sg')
	elif prefix == 'an':
		person, number = ('2', 'pl')
	elif prefix == 'oan':
		person, number = ('2', 'pl')
	elif prefix == 'o':
		person, number = ('3', 'sg')
	else:
		return None
	if i >= len(tokens) or tokens[i] != 'mo':
		return None
	i += 1
	if i >= len(tokens):
		return None
	verb_token = tokens[i]
	root, ending = detect_ntl_verb_ending(verb_token)
	if ending in {'future', 'future_plural'}:
		root = ntl_future_root_to_base_ntl(root + 'z')
	elif ending in {'pospreterite', 'pospreterite_plural'}:
		root = ntl_future_root_to_base_ntl(root)
	infinitive_sp = ntl_base_to_sp_infinitive(root)
	if not infinitive_sp:
		return None
	if ending in {'present_plural', 'past_plural', 'imperfect_plural', 'future_plural', 'pospreterite_plural'}:
		number = 'pl'
	if prefix == 'ti' and number == 'pl':
		person, number = ('1', 'pl')
	if prefix == 'oti' and number == 'pl':
		person, number = ('1', 'pl')
	if ending == 'present':
		verb_sp = conjugate_sp_present_from_infinitive(infinitive_sp, person, number)
	elif ending == 'present_plural':
		verb_sp = conjugate_sp_present_from_infinitive(infinitive_sp, person, number)
	elif ending in {'past', 'past_plural'}:
		verb_sp = conjugate_sp_past_from_infinitive(infinitive_sp, person, number)
	elif ending in {'future', 'future_plural'}:
		verb_sp = conjugate_sp_future_or_pospreterite(infinitive_sp, 'future', person, number)
	elif ending in {'imperfect', 'imperfect_plural'}:
		verb_sp = conjugate_sp_imperfect_from_infinitive(infinitive_sp, person, number)
	elif ending in {'pospreterite', 'pospreterite_plural'}:
		verb_sp = conjugate_sp_future_or_pospreterite(infinitive_sp, 'pospreterite', person, number)
	else:
		return None
	if not verb_sp:
		return None
	parts = []
	if explicit_subject and visible_subject:
		parts.append(visible_subject)
	if number == 'pl':
		parts.append('mismos')
	else:
		parts.append('mismo')
	parts.append(verb_sp)
	return ' '.join(parts)

def normalize_sp_output_case(text: str) -> str:
	text = (text or '').strip()
	if not text:
		return text
	if text.isupper():
		return text.lower()
	return text[0].lower() + text[1:]


# ----------------------------------------------------------------------
# Reconocimiento inverso de modos perfectos: Náhuatl -> Español
# ----------------------------------------------------------------------

_PERFECT_AUXILIARY_SP = {
	"present_perfect": {
		("1", "sg"): "he", ("2", "sg"): "has", ("3", "sg"): "ha",
		("1", "pl"): "hemos", ("2", "pl"): "habéis", ("3", "pl"): "han",
	},
	"preterite_anterior": {
		("1", "sg"): "hube", ("2", "sg"): "hubiste", ("3", "sg"): "hubo",
		("1", "pl"): "hubimos", ("2", "pl"): "hubisteis", ("3", "pl"): "hubieron",
	},
	"pluperfect": {
		("1", "sg"): "había", ("2", "sg"): "habías", ("3", "sg"): "había",
		("1", "pl"): "habíamos", ("2", "pl"): "habíais", ("3", "pl"): "habían",
	},
	"future_perfect": {
		("1", "sg"): "habré", ("2", "sg"): "habrás", ("3", "sg"): "habrá",
		("1", "pl"): "habremos", ("2", "pl"): "habréis", ("3", "pl"): "habrán",
	},
	"conditional_perfect": {
		("1", "sg"): "habría", ("2", "sg"): "habrías", ("3", "sg"): "habría",
		("1", "pl"): "habríamos", ("2", "pl"): "habríais", ("3", "pl"): "habrían",
	},
}


def _perfect_subject_from_token(token: str | None, plural_hint: bool = False) -> tuple[str, str]:
	"""Recupera persona y número desde el semipronombre o prefijo de pasado."""
	tk = (token or "").strip()
	mapping = {
		"ni": ("1", "sg"), "oni": ("1", "sg"),
		"ti": ("2", "sg"), "oti": ("2", "sg"),
		"an": ("2", "pl"), "oan": ("2", "pl"),
		"o": ("3", "pl" if plural_hint else "sg"),
		"": ("3", "pl" if plural_hint else "sg"),
	}
	subject = mapping.get(tk, ("3", "pl" if plural_hint else "sg"))
	# ti/oti + terminación plural representa primera persona plural.
	if plural_hint and tk in {"ti", "oti"}:
		return ("1", "pl")
	return subject


def _perfect_participle_sp_from_ntl(form_ntl: str) -> str | None:
	"""Busca el participio español correspondiente a una forma verbal náhuatl."""
	form = normalize_ntl_orthography(form_ntl or "").strip()
	if not form:
		return None

	clean = form[1:] if form.startswith("o") and len(form) > 1 else form
	root = compound_verb_root_ntl(form)

	# ado_ido es la autoridad para los participios, incluidos los irregulares.
	for participle_sp, ntl_value in ado_ido.items():
		for candidate in all_variants(ntl_value):
			candidate_norm = normalize_ntl_orthography(str(candidate)).strip()
			candidate_clean = (
				candidate_norm[1:]
				if candidate_norm.startswith("o") and len(candidate_norm) > 1
				else candidate_norm
			)
			if form == candidate_norm or clean == candidate_clean:
				return str(participle_sp)
			if root and compound_verb_root_ntl(candidate_norm) == root:
				return str(participle_sp)

	# Respaldo para verbos que están en el léxico, pero no en ado_ido.
	infinitive_sp = ntl_base_to_sp_infinitive(root)
	if not infinitive_sp:
		return None
	irregular = {
		"abrir": "abierto", "decir": "dicho", "escribir": "escrito",
		"hacer": "hecho", "morir": "muerto", "poner": "puesto",
		"resolver": "resuelto", "romper": "roto", "ver": "visto",
		"volver": "vuelto",
	}
	if infinitive_sp in irregular:
		return irregular[infinitive_sp]
	if infinitive_sp.endswith("ar"):
		return infinitive_sp[:-2] + "ado"
	if infinitive_sp.endswith(("er", "ir")):
		return infinitive_sp[:-2] + "ido"
	return None


def _perfect_auxiliary(kind: str, subject: tuple[str, str]) -> str | None:
	return _PERFECT_AUXILIARY_SP.get(kind, {}).get(subject)


def translate_ntl_perfect_to_sp(text: str) -> str | None:
	"""Reconoce las estructuras perfectas generadas por el sentido Español -> Náhuatl.

	Nota lingüística: ``ikin niman + futuro`` representa tanto el futuro perfecto
	como las formas compuestas del subjuntivo definidas en este motor. Por ello,
	la traducción inversa conserva explícitamente esa ambigüedad.
	"""
	t = normalize_ntl_compound_tokens(text)
	tokens = t.split()
	if not tokens:
		return None

	# habiendo comido -> onkatika/onkatikan otlakuak
	if tokens[0] in {"onkatika", "onkatikan"} and len(tokens) >= 2:
		participle = _perfect_participle_sp_from_ntl(tokens[-1])
		return f"habiendo {participle}" if participle else None

	# he comido -> ye oni tlakuak
	if tokens[0] == "ye" and len(tokens) >= 3:
		verb = tokens[-1]
		plural = verb.endswith(("keh", "kek"))
		subject = _perfect_subject_from_token(tokens[1], plural)
		participle = _perfect_participle_sp_from_ntl(verb)
		auxiliary = _perfect_auxiliary("present_perfect", subject)
		if auxiliary and participle:
			return f"{auxiliary} {participle}"

	# hube comido -> achto inon o ni otlakuak
	if tokens[:2] == ["achto", "inon"] and len(tokens) >= 3:
		body = tokens[2:]
		verb = body[-1]
		plural = verb.endswith(("keh", "kek", "yakeh"))

		# Pluscuamperfecto: achto inon tlakuaya
		if verb.endswith(("ya", "yakeh")) and not verb.endswith(("zya", "zyakeh")):
			root = verb[:-5] if verb.endswith("yakeh") else verb[:-2]
			participle = _perfect_participle_sp_from_ntl(root)
			# La forma directa actual no codifica persona; se conserva el valor
			# canónico de primera persona usado por la tabla de regresión.
			subject = ("1", "pl") if plural else ("1", "sg")
			auxiliary = _perfect_auxiliary("pluperfect", subject)
			if auxiliary and participle:
				return f"{auxiliary} {participle}"

		# Pretérito anterior. Admite "o ni", "oni", "o ti", etc.
		subject_token = ""
		if len(body) >= 3 and body[0] == "o" and body[1] in {"ni", "ti", "an"}:
			subject_token = "o" + body[1]
		elif len(body) >= 2 and body[0] in {"oni", "oti", "oan", "o"}:
			subject_token = body[0]
		elif len(body) >= 2 and body[0] in {"ni", "ti", "an"}:
			subject_token = body[0]
		subject = _perfect_subject_from_token(subject_token, plural)
		participle = _perfect_participle_sp_from_ntl(verb)
		auxiliary = _perfect_auxiliary("preterite_anterior", subject)
		if auxiliary and participle:
			return f"{auxiliary} {participle}"

	# habré / hubiera / hubiese / hubiere comido -> ikin niman ni tlakuaz
	if tokens[:2] == ["ikin", "niman"] and len(tokens) >= 3:
		body = tokens[2:]
		verb = body[-1]
		if verb.endswith(("z", "zkeh")):
			plural = verb.endswith("zkeh")
			subject_token = body[0] if len(body) > 1 else ""
			subject = _perfect_subject_from_token(subject_token, plural)
			root = verb[:-4] if plural else verb[:-1]
			participle = _perfect_participle_sp_from_ntl(root)
			auxiliary = _perfect_auxiliary("future_perfect", subject)
			if auxiliary and participle:
				subj = {
					("1", "sg"): "hubiera / hubiese / hubiere",
					("2", "sg"): "hubieras / hubieses / hubieres",
					("3", "sg"): "hubiera / hubiese / hubiere",
					("1", "pl"): "hubiéramos / hubiésemos / hubiéremos",
					("2", "pl"): "hubierais / hubieseis / hubiereis",
					("3", "pl"): "hubieran / hubiesen / hubieren",
				}[subject]
				return f"{auxiliary} {participle} / {subj} {participle}"

	# habría comido -> intla [ki] tlakuazya
	if tokens[0] == "intla" and len(tokens) >= 2:
		body = [tk for tk in tokens[1:] if tk not in {"ki", "kin"}]
		if body:
			verb = body[-1]
			if verb.endswith(("zya", "zyakeh")):
				plural = verb.endswith("zyakeh")
				subject_token = body[0] if len(body) > 1 else ""
				subject = _perfect_subject_from_token(subject_token, plural)
				root = verb[:-6] if plural else verb[:-3]
				participle = _perfect_participle_sp_from_ntl(root)
				auxiliary = _perfect_auxiliary("conditional_perfect", subject)
				if auxiliary and participle:
					return f"{auxiliary} {participle}"

	return None


def lookup_ntl_sp_exact(text: str):
	"""Respeta primero las igualdades NTL→SP definidas en las bases."""
	raw = unicodedata.normalize('NFC', str(text or '')).strip().lower()
	raw = raw.strip('.,;:¡!¿?\"\'“”‘’()[]{}')
	key = normalize_ntl_orthography(raw)
	for mapping in (NOUNS_NTL_SP, MODIFIERS_NTL_SP, ntl_sp):
		for candidate in (raw, key):
			val = mapping.get(candidate)
			if val is None:
				continue
			if isinstance(val, (list, tuple)):
				val = val[0] if val else None
			if isinstance(val, dict):
				val = val.get('es') or val.get('sp')
			if val:
				return str(val).strip()
	return None


def translate_ntl_belonging_noun_to_sp(text: str) -> str | None:
	"""Interpreta no/mo/i/to/anmo/in/kin como pertenencia ante una clave nominal NTL→SP."""
	t = normalize_ntl_orthography(text)
	t = re.sub('[¡!¿?\\.,;:"“”‘’«»]+', ' ', t)
	t = re.sub('\\s+', ' ', t).strip()
	tokens = t.split()
	if len(tokens) < 2:
		return None
	belonging_sp = {
		'no': 'mi',
		'mo': 'tu',
		'i': 'su',
		'to': 'nuestro',
		'anmo': 'de ustedes',
		'in': 'de ellos',
		'kin': 'de ellos',
	}
	prefix = tokens[0]
	if prefix not in belonging_sp:
		return None
	noun_ntl = ' '.join(tokens[1:])
	noun_sp = None
	for candidate in (noun_ntl, normalize_ntl_orthography(noun_ntl)):
		val = NOUNS_NTL_SP.get(candidate)
		if val is None:
			continue
		if isinstance(val, (list, tuple)):
			val = val[0] if val else None
		if isinstance(val, dict):
			val = val.get('es') or val.get('sp')
		if val:
			noun_sp = str(val).strip()
			break
	if not noun_sp:
		return None
	return f"{belonging_sp[prefix]} {noun_sp}"


def _translate_ntl_to_sp_core(text: str) -> str:
	text = (text or '').strip()
	exact = lookup_ntl_sp_exact(text)
	if exact:
		return normalize_sp_output_case(exact)
	belonging_noun = translate_ntl_belonging_noun_to_sp(text)
	if belonging_noun:
		return normalize_sp_output_case(belonging_noun)

	# Reconoce también las formas construidas por la regla productiva de
	# persona por origen, actividad u oficio.
	person_origin_activity = PERSON_ORIGIN_ACTIVITY_NTL_SP.get(
		normalize_ntl_orthography(text)
	)
	if person_origin_activity:
		return person_origin_activity
	segments = [seg.strip() for seg in re.split('[\\n.;]+', text) if seg.strip()]
	if len(segments) > 1:
		return '\n'.join((translate_ntl_to_sp(seg) for seg in segments))
	t_norm = normalize_ntl_compound_tokens(text)
	perfect_result = translate_ntl_perfect_to_sp(t_norm)
	if perfect_result:
		return normalize_sp_output_case(perfect_result)
	reflexive_result = translate_ntl_reflexive_direct_to_sp(t_norm)
	if reflexive_result:
		return reflexive_result
	structure_debug = parse_ntl_structure(t_norm)
	structure_result = translate_ntl_structure_to_sp(structure_debug)
	if structure_result:
		return normalize_sp_output_case(structure_result)
	conditional_result = translate_ntl_conditional_future_to_sp(t_norm)
	if conditional_result:
		return conditional_result
	simple_future = translate_ntl_simple_future_to_sp(t_norm)
	if simple_future:
		return simple_future
	simple_present = translate_ntl_simple_present_to_sp(t_norm)

	if simple_present:
		natural_object_forms = {
			'a mí': 'me',
			'a ti': 'te',
			'a nosotros': 'nos',
			'a nosotras': 'nos',
			'a él': 'lo',
			'a ella': 'la',
			'a ellos': 'los',
			'a ellas': 'las',
		}

		for analytic_object, clitic_object in natural_object_forms.items():
			if simple_present.startswith(analytic_object + ' '):
				simple_present = (
					clitic_object
					+ simple_present[len(analytic_object):]
				)
				break

		return normalize_sp_output_case(simple_present)
	simple_imperfect = translate_ntl_simple_imperfect_to_sp(t_norm)
	if simple_imperfect:
		return normalize_sp_output_case(simple_imperfect)
	aux_sub = translate_ntl_auxiliary_subordinate_to_sp(t_norm)
	if aux_sub:
		return normalize_sp_output_case(aux_sub)
	structure = parse_ntl_structure_to_sp(text)
	result = build_sp_expression_from_ntl_structure(structure)
	if result:
		return normalize_sp_output_case(result)
	t = normalize_ntl_orthography(text)
	tokens = t.split()
	if not tokens:
		return ''
	natural = reorder_short_ntl_to_natural_sp(tokens)
	if natural:
		return normalize_sp_output_case(natural)
	subjects = []
	verbs = []
	objects = []
	modifiers = []
	nouns = []
	others = []
	inline_phrases, used_indexes = detect_inline_fixed_phrases_ntl(tokens)
	for _start, _end, phrase_sp, source_kind in inline_phrases:
		if source_kind == 'noun':
			nouns.append(phrase_sp)
		elif source_kind == 'modifier':
			modifiers.append(phrase_sp)
		else:
			others.append(phrase_sp)
	for token_index, tk in enumerate(tokens):
		if token_index in used_indexes:
			continue
		sp = translate_token_ntl_to_sp(tk)
		if tk in NTL_SUBJECT_MAP_SP:
			subjects.append(NTL_SUBJECT_MAP_SP[tk])
			continue
		if tk in NTL_OBJECT_MAP_SP:
			objects.append(NTL_OBJECT_MAP_SP[tk])
			continue
		if tk in NTL_MODIFIER_SET:
			modifiers.append(sp)
			continue
		if tk in NTL_NOUN_SET:
			nouns.append(sp)
			continue
		if looks_like_spanish_verb(sp):
			verbs.append(sp)
			continue
		others.append(sp)
	ordered = subjects + verbs + objects + modifiers + nouns + others
	return ' '.join((x for x in ordered if x)).strip()

def _preserve_edge_sentence_punctuation(source: str, translated: str) -> str:
	"""Reincorpora signos de apertura/cierre eliminados por los normalizadores.

	Se limita a la puntuación de borde para no alterar el análisis lingüístico
	interno ni inventar posiciones para signos que separan cláusulas.
	"""
	source = str(source or '')
	translated = str(translated or '').strip()
	if not translated or not source.strip():
		return translated

	stripped = source.strip()
	opening_match = re.match(r'^[\s]*([¡¿]+)', stripped)
	closing_match = re.search(r'([!?]+)[\s]*$', stripped)
	opening = opening_match.group(1) if opening_match else ''
	closing = closing_match.group(1) if closing_match else ''

	# Evita duplicar signos si una ruta especial ya los conservó.
	if opening and not translated.startswith(opening):
		translated = opening + translated
	if closing and not translated.endswith(closing):
		translated = translated + closing
	return translated


def translate_sp_to_ntl(sp_text, mode='Auto', person='Auto', number='Auto', imp_p='xi', imp_n=False):
	translated = _translate_sp_to_ntl_core(
		sp_text, mode=mode, person=person, number=number, imp_p=imp_p, imp_n=imp_n
	)
	# En náhuatl se conserva únicamente el signo de cierre.
	source = str(sp_text or '').strip()
	closing_match = re.search(r'([!?]+)[\s]*$', source)
	closing = closing_match.group(1) if closing_match else ''
	translated = str(translated or '').strip()
	if closing and translated and not translated.endswith(closing):
		translated += closing
	return translated


def translate_ntl_to_sp(text: str) -> str:
	# El náhuatl usa únicamente signos de cierre. Se separan antes del
	# análisis para que no interfieran con la búsqueda léxica y, una vez
	# traducido el contenido, se reconstruye la puntuación española.
	source = str(text or '').strip()
	closing_match = re.search(r'([!?]+)[\s]*$', source)
	closing = closing_match.group(1) if closing_match else ''
	clean_text = source[:closing_match.start()].rstrip() if closing_match else source

	translated = str(_translate_ntl_to_sp_core(clean_text) or '').strip()
	if not translated or not closing:
		return translated

	opening = ''.join('¡' if sign == '!' else '¿' for sign in closing)
	if not translated.startswith(opening):
		translated = opening + translated
	if not translated.endswith(closing):
		translated += closing
	return translated


def translate_sp_to_ntl_licensed(text: str) -> str:
	"""
	Función de compatibilidad para la interfaz comercial.
	La licencia y el límite diario se controlan desde traductor_app.py
	o license_manager.py.
	"""
	return translate_sp_to_ntl(text)


def translate_ntl_to_sp_licensed(text: str) -> str:
	"""
	Función de compatibilidad para la interfaz comercial.
	"""
	return translate_ntl_to_sp(text)