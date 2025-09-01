gcloud pubsub subscriptions create bq-sub-user-interactions \
  --topic=user-interactions \
  --bigquery-table=myproject:analytics.user_interactions \
  --use-topic-schema