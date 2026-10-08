-- Ofertas encontradas y aun sin postular, para los scripts de prueba del bot.
create function public.empleo_ofertas_pendientes(p_plataforma text, p_min_score integer,
                                                 p_limite integer default 1)
returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  perform empleo.exigir_operador();
  return coalesce((
    select jsonb_agg(to_jsonb(o))
    from (
      select j.title, j.company_name, j.url, j.salary, j.location
      from empleo.jobs j
      where j.platform = p_plataforma and j.status = 'found' and j.match_score >= p_min_score
      order by j.match_score desc
      limit least(greatest(coalesce(p_limite, 1), 1), 50)
    ) o
  ), '[]'::jsonb);
end $$;

revoke all on function public.empleo_ofertas_pendientes(text, integer, integer) from public, anon;
grant execute on function public.empleo_ofertas_pendientes(text, integer, integer) to authenticated;
