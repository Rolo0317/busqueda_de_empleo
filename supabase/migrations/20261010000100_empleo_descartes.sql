-- Fase 3: memoria de descartes.
-- Las ofertas de otro oficio o fuera de zona se descartan solo por el titulo y
-- la ciudad. Antes se olvidaban al terminar el ciclo y se reevaluaban ~270 en
-- cada vuelta. La huella identifica la version de los filtros: si cambian las
-- reglas o el perfil, los descartes viejos dejan de contar y se reevaluan.

create table empleo.descartes (
  url        text primary key,
  motivo     text not null,
  huella     text not null,
  created_at timestamptz not null default now()
);
create index descartes_huella_idx on empleo.descartes (huella, created_at desc);
alter table empleo.descartes enable row level security;

-- Guarda un lote de descartes en un solo viaje. Un descarte repetido renueva
-- su huella y su fecha.
create function public.empleo_registrar_descartes(p_descartes jsonb) returns integer
language plpgsql volatile security definer set search_path = '' as $$
declare
  v_filas integer;
begin
  perform empleo.exigir_operador();
  insert into empleo.descartes (url, motivo, huella)
  select d ->> 'url', left(d ->> 'motivo', 200), d ->> 'huella'
  from jsonb_array_elements(coalesce(p_descartes, '[]'::jsonb)) d
  where coalesce(d ->> 'url', '') <> '' and coalesce(d ->> 'huella', '') <> ''
  on conflict (url) do update
    set motivo = excluded.motivo, huella = excluded.huella, created_at = now();
  get diagnostics v_filas = row_count;
  return v_filas;
end $$;

create function public.empleo_urls_descartadas(p_huella text, p_dias integer default 14) returns setof text
language plpgsql stable security definer set search_path = '' as $$
begin
  perform empleo.exigir_operador();
  return query
    select d.url from empleo.descartes d
    where d.huella = p_huella
      and d.created_at > now() - make_interval(days => least(greatest(coalesce(p_dias, 14), 1), 90));
end $$;

revoke all on function public.empleo_registrar_descartes(jsonb) from public, anon;
revoke all on function public.empleo_urls_descartadas(text, integer) from public, anon;
grant execute on function public.empleo_registrar_descartes(jsonb) to authenticated;
grant execute on function public.empleo_urls_descartadas(text, integer) to authenticated;
