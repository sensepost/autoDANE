#!/bin/bash

mysql autodane -Nse 'show tables;' | while read table; do mysql autodane -e "truncate table $table;" ; done;
