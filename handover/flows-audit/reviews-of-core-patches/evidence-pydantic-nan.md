# Evidence: pydantic NaN/Infinity handling in Route and load_config
Date 2026-11-16. EVIDENCE RUNNER: raw output, no judgement. Run with .venv python, made-up data, temp dir outside repo.

## Failures first (summary of raw facts below)
- Route accepts '0', '-1' and '0.0000001' (no positive/lower-bound check).
- First script run crashed in part 2 on a script bug (directory name clash for '-Infinity'); fixed and rerun; raw output of the rerun is below.

## Versions and pins
```
installed pydantic 2.14.1 pydantic-core 2.50.1
16:    "pydantic==2.14.1",
17:    "pydantic-settings==2.16.1",
1651:name = "pydantic"
1652-version = "2.14.1"
--
1666:name = "pydantic-core"
1667-version = "2.50.1"
--
1772:name = "pydantic-settings"
1773-version = "2.16.1"
```

## Code (src/hadavin_sdk/config.py lines 48-68)
```

def _money(v: object) -> object:
    if isinstance(v, float):
        # ValueError, not TypeError: pydantic turns only ValueError into a validation error.
        raise ValueError("money must be a decimal string, not a float")  # noqa: TRY004
    return v


Money = Annotated[Decimal, BeforeValidator(_money)]


class _Strict(BaseModel):
    # A mistyped key may hold a secret: errors name the field, never its value.
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class Route(_Strict):
    model_id: str
    input_usd_per_mtok: Money
    output_usd_per_mtok: Money
    max_tokens: int = Field(gt=0)
```

## Raw output of script (parts 1 and 2)
```
## PART 1: Route(...)
'NaN': REJECTED ValidationError: '2 validation errors for Route\ninput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number\noutput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number'
'Infinity': REJECTED ValidationError: '2 validation errors for Route\ninput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number\noutput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number'
'-Infinity': REJECTED ValidationError: '2 validation errors for Route\ninput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number\noutput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number'
'sNaN': REJECTED ValidationError: '2 validation errors for Route\ninput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number\noutput_usd_per_mtok\n  Input should be a finite number [type=finite_number]\n    For further information visit https://errors.pydantic.dev/2.14/v/finite_number'
'0': ACCEPTED in=Decimal('0') out=Decimal('0')
'-1': ACCEPTED in=Decimal('-1') out=Decimal('-1')
'0.0000001': ACCEPTED in=Decimal('1E-7') out=Decimal('1E-7')
## PART 2: load_config
-- NaN: substituted=True
    raise ConfigError(_validation_text(exc)) from exc
hadavin_sdk.errors.ConfigError: 2 validation errors for Config
routes.default.input_usd_per_mtok
  Input should be a finite number [type=finite_number]
    For further information visit https://errors.pydantic.dev/2.14/v/finite_number
routes.default.output_usd_per_mtok
  Input should be a finite number [type=finite_number]
    For further information visit https://errors.pydantic.dev/2.14/v/finite_number

-- Infinity: substituted=True
    raise ConfigError(_validation_text(exc)) from exc
hadavin_sdk.errors.ConfigError: 2 validation errors for Config
routes.default.input_usd_per_mtok
  Input should be a finite number [type=finite_number]
    For further information visit https://errors.pydantic.dev/2.14/v/finite_number
routes.default.output_usd_per_mtok
  Input should be a finite number [type=finite_number]
    For further information visit https://errors.pydantic.dev/2.14/v/finite_number

-- -Infinity: substituted=True
    raise ConfigError(_validation_text(exc)) from exc
hadavin_sdk.errors.ConfigError: 2 validation errors for Config
routes.default.input_usd_per_mtok
  Input should be a finite number [type=finite_number]
    For further information visit https://errors.pydantic.dev/2.14/v/finite_number
routes.default.output_usd_per_mtok
  Input should be a finite number [type=finite_number]
    For further information visit https://errors.pydantic.dev/2.14/v/finite_number

```
