select *
from {{ source('raw', 'sales_data') }}
