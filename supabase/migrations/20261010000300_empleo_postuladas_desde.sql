-- Fase 5: postulaciones recientes, para el tope diario y para no postular dos
-- veces a la misma oferta publicada en dos plataformas. La comparacion de
-- cargo y empresa se normaliza en Python, junto al resto de reglas del bot.

create function public.empleo_postuladas_desde(p_desde timestamptz) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  perform empleo.exigir_operador();
  return coalesce((
    select jsonb_agg(jsonb_build_object(
      'titulo', j.title, 'empresa', j.company_name, 'plataforma', j.platform, 'aplicada', a.applied_at
    ) order by a.applied_at desc)
    from empleo.applications a
    join empleo.jobs j on j.id = a.job_id
    where a.status = 'applied'
      and a.applied_at >= greatest(p_desde, now() - interval '180 days')
  ), '[]'::jsonb);
end $$;

revoke all on function public.empleo_postuladas_desde(timestamptz) from public, anon;
grant execute on function public.empleo_postuladas_desde(timestamptz) to authenticated;
