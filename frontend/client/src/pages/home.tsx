import { Search, TrendingUp, Clock, Star, Zap, Globe, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { 
  useLatestNews, 
  useTrending, 
  useSearchState, 
  useContentInteractions,
  useSummarization,
  useHealth,
  type ContentItem 
} from "../hooks/useSportsData";

export default function Home() {
  const [selectedSport, setSelectedSport] = useState<string>("");
  const [selectedArticle, setSelectedArticle] = useState<ContentItem | null>(null);
  const [showSummary, setShowSummary] = useState(false);

  // API hooks
  const { data: healthData } = useHealth();
  const { data: latestNews, isLoading: newsLoading, error: newsError } = useLatestNews(
    selectedSport ? [selectedSport.toLowerCase()] : undefined,
    12
  );
  const { data: trendingTerms, isLoading: trendingLoading } = useTrending(5);
  const { searchRequest, updateSearch, selectContent } = useSearchState();
  const { prefetchContent, shareContent } = useContentInteractions();
  const summarizationMutation = useSummarization({
    onSuccess: () => setShowSummary(true),
  });

  const categories = [
    { name: "NBA", icon: "🏀", sport: "basketball" },
    { name: "NFL", icon: "🏈", sport: "football" },
    { name: "MLB", icon: "⚾", sport: "baseball" },
    { name: "NHL", icon: "🏒", sport: "hockey" },
    { name: "SOCCER", icon: "⚽", sport: "soccer" },
    { name: "COLLEGE", icon: "🎓", sport: "college" },
    { name: "TENNIS", icon: "🎾", sport: "tennis" },
    { name: "GOLF", icon: "⛳", sport: "golf" },
    { name: "OLYMPICS", icon: "🏅", sport: "olympics" },
    { name: "ESPORTS", icon: "🎮", sport: "esports" }
  ];

  const inspirationTags = ["AI POWERED", "⚡ REAL-TIME", "PERSONALIZED"];

  // Handle article selection and summarization
  const handleArticleClick = async (article: ContentItem) => {
    setSelectedArticle(article);
    selectContent(article);
    
    // Generate AI summary
    summarizationMutation.mutate({
      content_ids: [article.id],
      summary_type: "brief",
      max_length: 150,
    });
  };

  // Handle sport category selection
  const handleSportSelect = (sport: string) => {
    setSelectedSport(selectedSport === sport ? "" : sport);
  };

  // Prefetch content on hover
  const handleArticleHover = (articleId: string) => {
    prefetchContent(articleId);
  };

  // Get display articles (API data or fallback)
  const displayArticles = latestNews?.items || [];

  // System status indicator
  const isSystemHealthy = healthData?.status === 'healthy';
  const isLiveData = latestNews?.engine !== 'mock';

  // Format time ago
  const formatTimeAgo = (dateString?: string) => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gray-bg">
      {/* Navigation Header */}
      <nav className="w-full px-6 py-4 bg-gray-bg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <div className="flex-shrink-0">
            <h1 className="text-xl font-black text-black tracking-tight">
              CORNER LEAGUE<sup className="text-sm">®</sup>
            </h1>
          </div>
          
          {/* System Status */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {isSystemHealthy ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-yellow-600" />
              )}
              <span className="text-xs font-medium text-gray-600">
                {isLiveData ? 'Live Data' : 'Demo Mode'}
              </span>
            </div>
            
            {/* Search Icon */}
            <button className="w-8 h-8 bg-black rounded-full flex items-center justify-center hover:bg-gray-800 transition-colors">
              <Search className="text-white w-3 h-3" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Container */}
      <div className="max-w-7xl mx-auto px-6">
        {/* Hero Section */}
        <section className="py-12">
          {/* Trending Section */}
          {!trendingLoading && trendingTerms && trendingTerms.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-4 h-4 text-red-500" />
                <span className="text-sm font-semibold text-black">TRENDING NOW</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {trendingTerms.slice(0, 5).map((term, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded-full hover:bg-red-100 transition-colors cursor-pointer"
                  >
                    {term.term} {term.is_trending && '🔥'}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Category Tags */}
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {categories.map((category, index) => (
              <span
                key={index}
                onClick={() => handleSportSelect(category.sport)}
                className={`px-3 py-1 text-xs font-medium border rounded-full transition-colors cursor-pointer ${
                  selectedSport === category.sport
                    ? 'bg-black text-white border-black'
                    : 'text-black border-black hover:bg-black hover:text-white'
                }`}
              >
                {category.icon} {category.name}
              </span>
            ))}
          </div>
          
          {/* Mission Statement */}
          <div className="text-center max-w-md mx-auto">
            <p className="text-sm font-medium text-black tracking-wide leading-relaxed">
              YOUR PERSONAL SPORTS ANALYST POWERED BY AI - GET THE SPORTS NEWS THAT MATTERS TO YOU.
            </p>
          </div>
        </section>
      </div>

      {/* Inspiration Quote Section */}
      <section className="bg-dark-section py-16 mb-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Quote Content */}
            <div className="space-y-8">
              <h2 className="text-4xl md:text-5xl font-light text-white font-serif leading-tight">
                Smart sports news that adapts to your passions.
              </h2>
              
              <p className="text-white opacity-90 text-base leading-relaxed max-w-lg">
                AI-powered curation finds the most relevant sports content from trusted sources, intelligently summarized and ranked by your favorite teams and interests.
              </p>
              
              {/* Tags */}
              <div className="flex flex-wrap gap-3">
                {inspirationTags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 text-xs font-medium text-white border border-white rounded-full hover:bg-white hover:text-black transition-colors cursor-pointer"
                  >
                    {tag}
                  </span>
                ))}
                <span className="w-8 h-8 bg-white rounded-full flex items-center justify-center hover:bg-gray-200 transition-colors cursor-pointer">
                  <svg className="w-3 h-3 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </div>
            
            {/* Image */}
            <div className="flex justify-center lg:justify-end">
              <img 
                src="https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&h=1000"
                alt="Sports analytics dashboard"
                className="w-64 h-80 object-cover object-center rounded-lg"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Article Preview Section */}
      <section className="max-w-7xl mx-auto px-6 pb-16">
        {/* Section Header */}
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-black">
            {selectedSport ? `${selectedSport.toUpperCase()} News` : 'Latest Sports News'}
          </h2>
          
          {newsLoading && (
            <div className="flex items-center gap-2 text-gray-600">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Loading...</span>
            </div>
          )}
          
          {latestNews && (
            <div className="text-sm text-gray-600">
              {latestNews.total_count} articles • {latestNews.search_time_ms}ms
            </div>
          )}
        </div>

        {/* Error State */}
        {newsError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium text-red-800">
                Unable to load latest news. Showing cached content.
              </span>
            </div>
          </div>
        )}

        {/* Articles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {displayArticles.map((article) => (
            <article 
              key={article.id} 
              className="group cursor-pointer bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
              onClick={() => handleArticleClick(article)}
              onMouseEnter={() => handleArticleHover(article.id)}
            >
              <div className="relative">
                <img 
                  src={article.image_url || "https://images.unsplash.com/photo-1546519638-68e109498ffc?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&h=600"}
                  alt={article.title}
                  className="w-full h-48 object-cover rounded-t-lg group-hover:opacity-90 transition-opacity"
                />
                
                {/* Quality Score Badge */}
                <div className="absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded-full">
                  {Math.round(article.quality_score * 100)}%
                </div>
                
                {/* Time Badge */}
                {article.published_at && (
                  <div className="absolute bottom-2 left-2 bg-white bg-opacity-90 text-black text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTimeAgo(article.published_at)}
                  </div>
                )}
              </div>
              
              <div className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-gray-600">{article.source_name}</span>
                  {article.sports_keywords.length > 0 && (
                    <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                      {article.sports_keywords[0]}
                    </span>
                  )}
                </div>
                
                <h3 className="text-lg font-semibold text-black mb-2 group-hover:text-gray-700 transition-colors line-clamp-2">
                  {article.title}
                </h3>
                
                {article.summary && (
                  <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                    {article.summary}
                  </p>
                )}
                
                {article.byline && (
                  <p className="text-xs text-gray-500">
                    {article.byline}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>

        {/* Load More Button */}
        {latestNews?.has_more && (
          <div className="text-center mt-8">
            <button className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
              Load More Articles
            </button>
          </div>
        )}
      </section>

      {/* AI Summary Modal */}
      {selectedArticle && showSummary && summarizationMutation.data && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-xl font-bold text-black pr-4">
                  AI Summary
                </h3>
                <button 
                  onClick={() => setShowSummary(false)}
                  className="text-gray-500 hover:text-black"
                >
                  ✕
                </button>
              </div>
              
              <div className="mb-4">
                <h4 className="font-semibold text-gray-900 mb-2">{selectedArticle.title}</h4>
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
                  <span>{selectedArticle.source_name}</span>
                  <span>•</span>
                  <span>{formatTimeAgo(selectedArticle.published_at)}</span>
                  <span>•</span>
                  <span>Quality: {Math.round(selectedArticle.quality_score * 100)}%</span>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-gray-900">AI-Generated Summary</span>
                  <span className="text-xs text-gray-600">
                    Confidence: {Math.round(summarizationMutation.data.confidence_score * 100)}%
                  </span>
                </div>
                <p className="text-gray-800 leading-relaxed">
                  {summarizationMutation.data.summary}
                </p>
              </div>
              
              {summarizationMutation.data.key_entities && summarizationMutation.data.key_entities.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Key Entities</h5>
                  <div className="flex flex-wrap gap-2">
                    {summarizationMutation.data.key_entities.map((entity, index) => (
                      <span key={index} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex items-center justify-between pt-4 border-t">
                <div className="text-xs text-gray-500">
                  Generated in {Math.round(summarizationMutation.data.generation_time_ms)}ms
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => shareContent(selectedArticle)}
                    className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    Share
                  </button>
                  <a 
                    href={selectedArticle.canonical_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 text-sm bg-black text-white rounded hover:bg-gray-800 transition-colors"
                  >
                    Read Full Article
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay for summarization */}
      {summarizationMutation.isPending && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-gray-900">Generating AI summary...</span>
          </div>
        </div>
      )}
    </div>
  );
}

