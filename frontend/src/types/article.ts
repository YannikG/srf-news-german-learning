export type ArticleListItem = {
  id: number;
  external_id: string;
  publisher: string | null;
  provenance: string | null;
  title: string;
  lead: string | null;
  release_date: string;
  modification_date: string | null;
  cefr_level: string | null;
  created_at: string;
  updated_at: string;
};

export type ArticlesListResponse = {
  items: ArticleListItem[];
  next_cursor: string | null;
};

export type ArticleDetail = ArticleListItem & {
  markdown_original: string;
  markdown_simplified: string | null;
  simplification_cefr_level: string | null;
};

export type NewsRefreshSuccess = {
  fetched: boolean;
  articles_upserted: number;
  next_allowed_fetch_at: string;
};
