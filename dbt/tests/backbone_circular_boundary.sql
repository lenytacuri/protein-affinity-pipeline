{{ config(tags=['backbone']) }}
-- depends_on: {{ ref('backbone_features') }}
-- Boundary fixture: 179 and -179 must average near 180, not zero.
with angles as (select column1::double as x from values (179),(-179)),
a as (select avg(sin(radians(x))) as s,avg(cos(radians(x))) as c from angles)
select 'incorrect_circular_mean' as issue from a
where abs(abs(degrees(atan2(s,c)))-180)>1e-8 or sqrt(s*s+c*c)<0.999
