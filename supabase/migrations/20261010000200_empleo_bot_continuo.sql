-- Fase 4: el bot continuo vigilado por un supervisor en la PC.
-- El supervisor late cada 30 s con el estado del bot; el panel lee ese estado,
-- alerta si no hay actividad y puede pausar el reinicio automatico.

create table empleo.bot_continuo (
  machine      text primary key,
  latido_at    timestamptz not null default now(),  -- ultima senal del supervisor
  actividad_at timestamptz,                          -- ultima linea escrita en el log del bot
  proceso_vivo boolean not null default false,
  reinicios    integer not null default 0,           -- desde que arranco el supervisor
  ultimo_ciclo text,                                 -- linea RESUMEN CICLO mas reciente
  pausado      boolean not null default false        -- lo decide el panel
);
alter table empleo.bot_continuo enable row level security;

-- Plazos compartidos por el supervisor y el panel.
create function empleo.minutos_bot_inactivo() returns integer
language sql immutable set search_path = '' as $$ select 30 $$;

create function empleo.segundos_supervisor_en_linea() returns integer
language sql immutable set search_path = '' as $$ select 180 $$;

-- Latido del supervisor. Devuelve si el panel pidio pausar el bot.
create function public.empleo_latido_bot(p_maquina text, p_estado jsonb) returns boolean
language plpgsql volatile security definer set search_path = '' as $$
declare
  v_pausado boolean;
begin
  perform empleo.exigir_operador();
  insert into empleo.bot_continuo as b (machine, latido_at, actividad_at, proceso_vivo, reinicios, ultimo_ciclo)
  values (p_maquina, now(), (p_estado ->> 'actividad_at')::timestamptz,
          coalesce((p_estado ->> 'proceso_vivo')::boolean, false),
          coalesce((p_estado ->> 'reinicios')::integer, 0), p_estado ->> 'ultimo_ciclo')
  on conflict (machine) do update
    set latido_at = now(), actividad_at = excluded.actividad_at, proceso_vivo = excluded.proceso_vivo,
        reinicios = excluded.reinicios, ultimo_ciclo = coalesce(excluded.ultimo_ciclo, b.ultimo_ciclo)
  returning b.pausado into v_pausado;
  return v_pausado;
end $$;

-- Estado para el panel, con la alerta ya decidida en un solo lugar.
create function public.empleo_estado_bot() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  perform empleo.exigir_operador();
  return coalesce((
    select jsonb_build_object(
      'maquina', b.machine,
      'latido', b.latido_at,
      'actividad', b.actividad_at,
      'procesoVivo', b.proceso_vivo,
      'reinicios', b.reinicios,
      'ultimoCiclo', b.ultimo_ciclo,
      'pausado', b.pausado,
      'alerta', case
        when b.latido_at < now() - make_interval(secs => empleo.segundos_supervisor_en_linea())
          then 'supervisor_apagado'
        when b.pausado then null
        when not b.proceso_vivo then 'bot_detenido'
        when b.actividad_at is null
          or b.actividad_at < now() - make_interval(mins => empleo.minutos_bot_inactivo())
          then 'sin_actividad'
      end
    )
    from empleo.bot_continuo b order by b.latido_at desc limit 1
  ), jsonb_build_object('alerta', 'supervisor_apagado'));
end $$;

create function public.empleo_pausar_bot(p_pausado boolean) returns void
language plpgsql volatile security definer set search_path = '' as $$
begin
  perform empleo.exigir_operador();
  update empleo.bot_continuo set pausado = p_pausado;
end $$;

revoke all on function public.empleo_latido_bot(text, jsonb) from public, anon;
revoke all on function public.empleo_estado_bot() from public, anon;
revoke all on function public.empleo_pausar_bot(boolean) from public, anon;
grant execute on function public.empleo_latido_bot(text, jsonb) to authenticated;
grant execute on function public.empleo_estado_bot() to authenticated;
grant execute on function public.empleo_pausar_bot(boolean) to authenticated;
